from num2words import num2words
import os
import yaml
from loguru import logger
from dateutil.parser import parse
from datetime import datetime
from tinydb import TinyDB, Query
import random

# Initialisiere Datenbankzugriff auf Modulebene
reminder_db = TinyDB(os.path.join('intents','functions','reminder','reminder_db.json'))
reminder_table = reminder_db.table('reminder')

path = os.path.join('intents','functions','reminder','config_reminder.yml')
try:
    with open(path, "r", encoding="utf8") as file:
        config_reminder = yaml.load(file, Loader=yaml.FullLoader)
except Exception as e:
    logger.error("Konnte config_reminder.yml nicht laden, Fehler: {}", e)


def callback(processed = False, language = "de"):
    for reminder in reminder_table.all():
        parsed_time = parse(reminder["time"])  
              
        if parsed_time <= datetime.now(parsed_time.tzinfo):
            if processed:
                logger.info('Der Reminder am {} mit Inhalt {} wird nun gelöscht.', reminder['time'], reminder['msg'])
                Reminder_Query = Query()
                reminder_table.remove(Reminder_Query.time == reminder['time'] and Reminder_Query.msg == reminder['msg'] and Reminder_Query.kind == reminder['kind'])
                return None
            
            if reminder["kind"] == "inf":
                reminder_text = random.choice(config_reminder['intent']['reminder'][language]['execute_reminder_infinitive'])
                return reminder_text.format(reminder['msg'])
            if reminder["kind"] == "to":
                reminder_text = random.choice(config_reminder['intent']['reminder'][language]['execute_reminder_to'])
                return reminder_text.format(reminder['msg'])
            return random.choice(config_reminder['intent']['reminder'][language]['execute_reminder'])
    return None
        



def extract_date(datetime, lang):
	hours = str(datetime.hour)
	minutes = "" if datetime.minute == 0 else str(datetime.minute)
	day = num2words(datetime.day, lang=lang, to="ordinal")
	month = num2words(datetime.month, lang=lang, to="ordinal")
	year = "" if datetime.year == datetime.now().year else str(datetime.year)
	
	# Anpassung an den deutschen Casus
	if lang == 'de':
		day += 'n'
		month += 'n'
		
	return hours, minutes, day, month, year

def reminder(language = "de", time = None, reminder_to=None, reminder_infinitive=None):
    if time is None:
        logger.error("Konnte Zeit nicht auslesen.")
        return random.choice(config_reminder['intent']['reminder'][language]['exception'])
    parsed_time = parse(time)
    hours, minutes, day, month, year = extract_date(parsed_time, language)
    
    if datetime.now().date() == parsed_time.date():
        if reminder_to:
            message = random.choice(config_reminder['intent']['reminder'][language]['reminder_same_day_to'])
            reminder_table.insert({'time':time, 'kind':'to', 'msg':reminder_to})
            return message.format(hours, minutes, reminder_to)
        if reminder_infinitive:
            message = random.choice(config_reminder['intent']['reminder'][language]['reminder_same_day_infinitive'])
            reminder_table.insert({'time':time, 'kind':'inf', 'msg':reminder_infinitive})
            return message.format(hours, minutes, reminder_infinitive)
        
        # Es wurde nicht angegeben, an was erinnert werden soll
        message = random.choice(config_reminder['intent']['reminder'][language]['reminder_same_day_no_action'])
        reminder_table.insert({'time':time, 'kind':'none', 'msg':''})
        return message.format(hours, minutes)
    
    # Datum ist nicht heute
    if reminder_to:
        message = random.choice(config_reminder['intent']['reminder'][language]['reminder_to'])
        reminder_table.insert({'time':time, 'kind':'to', 'msg':reminder_to})
        return message.format(day, month, year, hours, minutes, reminder_to)
    if reminder_infinitive:
        message = random.choice(config_reminder['intent']['reminder'][language]['reminder_infinitive'])
        reminder_table.insert({'time':time, 'kind':'inf', 'msg':reminder_infinitive})
        return message.format(day, month, year, hours, minutes, reminder_infinitive)
    
    # Es wurde nicht angegeben, an was erinnert werden soll
    message = random.choice(config_reminder['intent']['reminder'][language]['reminder_no_action'])
    reminder_table.insert({'time':time, 'kind':'none', 'msg':''})
    return message.format(day, month, year, hours, minutes)