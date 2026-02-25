import caldav
import json
from datetime import datetime, timedelta
import requests
from icalendar import Calendar, Event, Alarm
from pathlib import Path
import pytz


class CalendarSyncManager:
    def __init__(self, config_file='events.json'):
        """Inicializa el gestor de sincronización de calendarios"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Conectar a CalDAV
        self.client = caldav.DAVClient(
            url=self.config['caldav']['url'],
            username=self.config['caldav']['username'],
            password=self.config['caldav']['password']
        )
        self.principal = self.client.principal()
        
    def get_or_create_calendar(self, calendar_name):
        """Obtiene o crea un calendario por nombre"""
        calendars = self.principal.calendars()
        
        # Buscar calendario existente
        for cal in calendars:
            if cal.name == calendar_name:
                print(f"📋 Usando calendario existente: {calendar_name}")
                return cal
        
        # Crear si no existe
        print(f"🆕 Creando nuevo calendario: {calendar_name}")
        try:
            new_cal = self.principal.make_calendar(name=calendar_name)
            print(f"✅ Calendario creado exitosamente")
            return new_cal
        except Exception as e:
            print(f"❌ Error creando calendario: {e}")
            # Intenta con el primer calendario disponible
            if calendars:
                print(f"⚠️  Usando primer calendario disponible: {calendars[0].name}")
                return calendars[0]
            raise
    
    def get_existing_events_uids(self, calendar):
        """Obtiene todos los UIDs de eventos existentes en el calendario (optimizado)"""
        try:
            events = calendar.events()
            uids = {}
            for event in events:
                ical = Calendar.from_ical(event.data)
                for component in ical.walk('VEVENT'):
                    uid = str(component.get('UID'))
                    uids[uid] = event
            return uids
        except:
            return {}
    
    def convert_to_spain_time(self, dt):
        """Convierte cualquier datetime a la zona horaria de España (Europe/Madrid)"""
        spain_tz = pytz.timezone('Europe/Madrid')
        
        # Si el datetime es naive (sin zona horaria), asume UTC
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            dt = pytz.utc.localize(dt)
        
        # Convertir a hora de España
        return dt.astimezone(spain_tz)
    
    def create_event_with_alarms(self, summary, dtstart, dtend, description, uid, location=''):
        """Crea un evento iCalendar con alarmas de 15 y 5 minutos"""
        cal = Calendar()
        cal.add('prodid', '-//Synology Calendar Sync//ES')
        cal.add('version', '2.0')
        
        event = Event()
        event.add('summary', summary)
        event.add('dtstart', dtstart)
        event.add('dtend', dtend)
        event.add('dtstamp', datetime.now())
        event.add('uid', uid)
        
        if description:
            event.add('description', str(description))
        if location:
            event.add('location', location)
        
        # Alarma 15 minutos antes
        alarm15 = Alarm()
        alarm15.add('action', 'DISPLAY')
        alarm15.add('trigger', timedelta(minutes=-15))
        alarm15.add('description', f'Recordatorio: {summary}')
        event.add_component(alarm15)
        
        # Alarma 5 minutos antes
        alarm5 = Alarm()
        alarm5.add('action', 'DISPLAY')
        alarm5.add('trigger', timedelta(minutes=-5))
        alarm5.add('description', f'Recordatorio: {summary}')
        event.add_component(alarm5)
        
        cal.add_component(event)
        return cal.to_ical().decode('utf-8')
    
    def sync_calendar(self, calendar_name, ics_url):
        """Sincroniza un calendario desde una URL ICS"""
        print(f"\n🔄 Sincronizando calendario: {calendar_name}")
        
        # Descargar ICS
        try:
            response = requests.get(ics_url, timeout=30)
            response.raise_for_status()
            ics_data = response.text
        except Exception as e:
            print(f"❌ Error descargando ICS: {e}")
            return
        
        # Obtener calendario destino
        calendar = self.get_or_create_calendar(calendar_name)
        
        # Obtener eventos existentes (una sola vez - optimización)
        existing_events = self.get_existing_events_uids(calendar)
        print(f"📊 Eventos existentes: {len(existing_events)}")
        
        # Obtener fecha actual en hora de España
        spain_tz = pytz.timezone('Europe/Madrid')
        now = datetime.now(spain_tz)
        
        # Parsear ICS
        cal = Calendar.from_ical(ics_data)
        events_to_sync = []
        past_events_count = 0
        
        for component in cal.walk('VEVENT'):
            uid = str(component.get('UID'))
            summary = str(component.get('SUMMARY', 'Sin título'))
            dtstart = component.get('DTSTART').dt
            dtend = component.get('DTEND').dt if component.get('DTEND') else dtstart
            description = component.get('DESCRIPTION', '')
            location = component.get('LOCATION', '')
            
            # Convertir a hora de España si es datetime (no date)
            if isinstance(dtstart, datetime):
                dtstart = self.convert_to_spain_time(dtstart)
            if isinstance(dtend, datetime):
                dtend = self.convert_to_spain_time(dtend)
            
            # Filtrar eventos pasados
            event_end = dtend if dtend else dtstart
            if isinstance(event_end, datetime):
                # Es datetime con hora
                if event_end < now:
                    past_events_count += 1
                    continue
            else:
                # Es date sin hora - comparar solo fechas
                if event_end < now.date():
                    past_events_count += 1
                    continue
            
            events_to_sync.append({
                'uid': uid,
                'summary': summary,
                'dtstart': dtstart,
                'dtend': dtend,
                'description': description,
                'location': location
            })
        
        if past_events_count > 0:
            print(f"⏭️  Eventos pasados omitidos: {past_events_count}")
        print(f"📥 Eventos futuros a sincronizar: {len(events_to_sync)}")
        
        # Sincronizar eventos
        added = 0
        updated = 0
        
        for event_data in events_to_sync:
            uid = event_data['uid']
            ical_str = self.create_event_with_alarms(
                event_data['summary'],
                event_data['dtstart'],
                event_data['dtend'],
                event_data['description'],
                uid,
                event_data['location']
            )
            
            if uid in existing_events:
                # Actualizar evento existente
                try:
                    existing_events[uid].data = ical_str
                    existing_events[uid].save()
                    updated += 1
                except Exception as e:
                    print(f"⚠️  Error actualizando {event_data['summary']}: {e}")
            else:
                # Crear nuevo evento
                try:
                    calendar.save_event(ical_str)
                    added += 1
                except Exception as e:
                    print(f"⚠️  Error creando {event_data['summary']}: {e}")
        
        print(f"✅ Completado: {added} añadidos, {updated} actualizados")
    
    def sync_all(self):
        """Sincroniza todos los calendarios configurados"""
        print("=" * 60)
        print(f"🚀 Iniciando sincronización - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        for cal_config in self.config['calendarios']:
            self.sync_calendar(cal_config['nombre'], cal_config['url_ics'])
        
        print("\n" + "=" * 60)
        print("✨ Sincronización completada")
        print("=" * 60)


if __name__ == '__main__':
    manager = CalendarSyncManager('events.json')
    manager.sync_all()