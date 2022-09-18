"""
This program buils a Discord Bot that helps users to set up their tasks with specified deadlines and reminders if needed.
The main functions include: add task, remove task, see tasklist, set reminder, check deadline, check task.
"""

#from keep_alive import keep_alive

import discord, asyncio, pytz, time, requests, random, pyaztro, os,uuid
import datetime as dt
from datetime import datetime,date, timedelta,timezone
from discord.ext import commands
from replit import db #import database

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(intents = intents,command_prefix = '.')

timezone_VN = pytz.timezone('Asia/Ho_Chi_Minh')

def update_task(new_task, deadline, user):
  '''This function helps add a new task to the database
  Parameters:
    new_task - string: the name of the task
    deadline - string: the date of the deadline
    user - string: the name of the assigned person
  Return:
    nothing, only update data to the database'''
    
  info = {}
  info['Deadline'] = deadline
  info['User'] = user
  db[new_task] = info

def delete_task(task):
  '''This function helps delete an exising task
  Parameter:
    task - string: the name of the task
  Return:
    a message to inform the status of user' command'''
  
  if task in db:
    del db[task]
    return '`Task removed!`'
  else:
    return "`Task doesn't exist. Please try again!`"
  
def make_pretty_dic(dict_):
  '''This function helps convert a dictionary into a pretty string for sending message back to user
  Parameter:
    dict_ - dictionary: the database
  Return:
    pretty_dic - string: a pretty version of the database'''

  pretty_dic = ''
  
  today = dt.datetime.now(timezone_VN)
  today = today.strftime("%d-%m-%Y %H:%M")
  today = dt.datetime.strptime(today, "%d-%m-%Y %H:%M")
  
  for i in dict_:
    deadline = dict_[i]['Deadline']
    deadline_dt = dt.datetime.strptime(deadline, "%d-%m-%Y %H:%M")

    if deadline_dt < today:
      status = " **|** `Expired`"
    elif deadline_dt > today:
      status = " **|** `In Progress`"
    
    pretty_dic = (pretty_dic + "\r\n" + i + ' - ' + '`Deadline:` ' + dict_[i]['Deadline'] + ', `Assigned for:` ' + dict_[i]['User'] + status)

  return pretty_dic

def check_time_left(task):
  '''This function helps check time left of a task
  Parameters:
    task - string: the name of the task
  Return:
    a message to inform the amount of time left to finish the task'''

  deadline = db[task]['Deadline']
  deadline_dt = dt.datetime.strptime(deadline, "%d-%m-%Y %H:%M")
  today = dt.datetime.now(timezone_VN)
  today = today.strftime("%d-%m-%Y %H:%M")
  today = dt.datetime.strptime(today, "%d-%m-%Y %H:%M")
  
  time_left = deadline_dt - today
  if time_left.days < 0:
    noti = '**This task was expired**'
  elif time_left.days == 0:
    noti = (':pushpin: **You have** ' + str(time_left)[-8:-6] + ' hours' + ' and ' + str(time_left)[-5:-3] + ' minutes **left to finish** ' + task)
  else:
    noti = (':pushpin: **You have** ' + str(time_left)[:-9] + ', ' + str(time_left)[-8:-6] + ' hours' + ' and ' + str(time_left)[-5:-3] + ' minutes **left to finish** ' + task)
  
  return noti

def convert_deadline_db_to_date(task):
  '''This function helps convert the string deadline in database into date
  Parameter:
    task - string: the name of the task
  Return:
    deadline - a date format of the deadline'''

  deadline = ((db[task]['Deadline'].split(' '))[0]).split('-')
  deadline = date(int(deadline[-1]),int(deadline[1]),int(deadline[0]))
  
  return deadline


@client.event
async def on_ready():
  '''This function prints a message if bot is successfully launched'''
  print('Your bot is ready!')


@client.event
async def on_message(message):
    '''THIS IS THE MAIN FUNCTION THAT HELPS BOT TO RESPOND TO CERTAIN MESSAGES OF USER.
    IF THE MESSAGE OF THE USER CONTAINS THE DEFINED WORDS (COMMANDS), BOT WILL FUNCTION ACCORDINGLY'''
    
    if message.author == client.user:
        return

    msg = message.content


    if msg.startswith("!howlong"):
      '''THIS COMMAND IS TO CHECK THE AMOUNT OF TIME LEFT UNTIL A DEADLINE'''

      task = str(msg.split("!howlong ",1)[1])
      if task in db:
        embed = discord.Embed(description=check_time_left(task),color=0xff0000,timestamp=dt.datetime.utcnow())
        await message.channel.send(embed = embed)
      else:
        await message.channel.send("`Task doesn't exist. Please try again!`")
    

    if msg.startswith("!add"):
        '''THIS COMMAND IS TO ADD A NEW TASK WITH DEADLINE AND TO ASSIGN PEOPLE IF NEEDED'''

        new_task = msg.split("!add ",1)[1]       

        await message.channel.send('Set your deadline in format `DD-MM-YYYY 00:00` _(e.g., 14-01-2022 19:07)_:')

        def check_deadline(deadline):
            '''condition for inputtin deadline'''

            try:
              '''if the input is DD-MM-YYYY'''
              deadline_content = deadline.content
              deadline_day = datetime.strptime(deadline_content, '%d-%m-%Y %H:%M').date()
              
            except ValueError:
              return False

            else:
              return deadline.author == message.author

        def check_user(user):
          '''condition for inputting user'''
          return deadline.author == message.author
          
        try:
          deadline = await client.wait_for('message', timeout=20.0, check=check_deadline)
        except asyncio.TimeoutError:
          await message.channel.send('`You took too long to enter. Fail to add new task!`')
        else:
          await message.channel.send('This task is assigned for:') 
          try:
            user = await client.wait_for('message', timeout=10.0,check = check_user) 
                #user = msg[3:-1]
          except asyncio.TimeoutError:
            await message.channel.send('`You took too long to enter. Fail to add new task!`')
            return
          else:  
            user = user.content
            deadline = deadline.content
            update_task(new_task, deadline, user)
            await message.channel.send('`Task & Deadline & Username added!`')


    if msg == '!task':
        '''THIS COMMAND IS TO SEE ALL THE CURRENT TASKS'''

        pretty_dic = make_pretty_dic(db)
        embed = discord.Embed(title=':page_facing_up: Current task list',description=pretty_dic,color=0xffc800)
        await message.channel.send(embed = embed)

    
    if msg.startswith('!taskuser'):
      '''THIS COMMAND IS TO SEE ALL THE CURRENT TASKS ASSIGNED FOR A SPECIFIC PERSON'''

      user = msg.split('!taskuser ',1)[1]
      lst_task_user = {}
      for i in db:
        if db[i]['User'] == user:
          lst_task_user[i] = db[i]
      pretty_dic = make_pretty_dic(lst_task_user)
      embed = discord.Embed(title='Current task list for user ' + user,description=pretty_dic,color=0xffc800)
      await message.channel.send(embed = embed)


    if msg.startswith('!remove'):
        '''THIS COMMAND IS TO REMOVE AN EXISTING TASK'''
       
        task_list = []
        pretty_dic = ''
        
        task = str(msg.split("!remove ",1)[1])
       
        await message.channel.send(delete_task(task))
      
        pretty_dic = make_pretty_dic(db)
        
        embed = discord.Embed(title=':page_facing_up: Current task list',description=pretty_dic,color=0xffc800)
        await message.channel.send(embed = embed)

    
    if msg.startswith("!reminder"):
      '''THIS COMMAND IS TO SET REMINDER FOR AN EXISTING TASK'''

      task = str(msg.split("!reminder ",1)[1])
      if task in db:
        embed = discord.Embed(
          title = "Reminder function",
          description = ""
        )
        
        embed.add_field(name = "`auto`", value = "To get reminded every 5 hours, type `auto`", inline = False)

        embed.add_field(name = "`custom`", value = "To set the interval for the reminder, type `custom`", inline = False)

        embed.add_field(name = "`remind me in`", value = "To get reminded in set time, type `remind me in n [days/hours/minutes]`", inline = False)

        embed.add_field(name = "`remind me at`", value = "To get reminded at a specific time, type `remind me at DD-MM-YYYY HH:MM`", inline = False)

        embed.add_field(name = "`remind me before`", value = "To get reminded before the deadline, type `remind me n [days/hours/minutes] before`", inline = False)

        await message.channel.send(embed = embed)
        await message.channel.send('Set the type of reminder:')

        def check_type(type_reminder):
          '''Adds option for a reminder at a customized time for the user'''
          tr_c = type_reminder.content
          return (tr_c == 'custom' or tr_c =='auto' or tr_c.startswith('remind me in') or tr_c.startswith('remind me at') or (tr_c.startswith('remind me') and tr_c.endswith('before')) ) and type_reminder.author == message.author 
 
        def check_interval(interval):
          return  type_reminder.author == message.author and (
              (interval.content.split()[-1]) == 'hours' or (interval.content.split()[-1]) == 'minutes' or (interval.content.split()[-1]) == 'min' or (interval.content.split()[-1]) == 'days'
              )

        try:
          type_reminder = await client.wait_for('message', timeout=20.0,check=check_type)
        except asyncio.TimeoutError:
          await message.channel.send('`You took too long to enter. Fail to add new reminder!`')
        else:
            type_content = type_reminder.content
            deadline = db[task]['Deadline']
            pattern = '%d-%m-%Y %H:%M'     
            deadline = timezone_VN.localize(datetime.strptime(deadline, pattern))

            starting_time = datetime.now()
            now = datetime.now().astimezone(timezone_VN)

            if type_content == "auto":
              if deadline < now:
                await message.channel.send("`The deadline has already passed, please re-add the task`")
              else:
                await message.channel.send('`You will be reminded every 5 hours from now`')
                while now < deadline:
                  await asyncio.sleep(18000)
                  await message.channel.send(task + " - " + db[task]['User'])
                  now = datetime.now().astimezone(timezone_VN)

            elif type_content == "custom":
              embed = discord.Embed(
                title = "`Reminding in every set interval`",
                description = ""
              )
              
              embed.add_field(name = "`minutes` or `min`", value = "To get reminded every n hours, type `n minutes`", inline = False)

              embed.add_field(name = "`hours`", value = "To get reminded every n hours, type `n hours`", inline = False)

              embed.add_field(name = "`days`", value = "To get reminded every n hours, type `n days`", inline = False)

              await message.channel.send(embed = embed)
              await message.channel.send('`Set your interval in minutes/hours/days (e.g., 3.5 hours)`')
              try:
                interval = await client.wait_for('message', timeout=10.0, check=check_interval)
              except asyncio.TimeoutError:
                await message.channel.send("`You took too long to enter. Fail to add new reminder!`")
              else: 
                interval_content = interval.content.split()
                interval = float(interval_content[0])
                time_type = interval_content[-1]

                if time_type == 'minutes' or time_type == 'min':
                  interval = interval *60
                elif time_type == 'hours':
                  interval = interval * 3600
                elif time_type == 'days':
                  interval = interval * 3600*24
                if deadline < now:
                  await message.channel.send("`The deadline has already passed, please re-add the task`")
                else:
                  await message.channel.send('`You will be reminded every` ' + str(interval_content) + ' ' + time_type + ' `from now`')
                  while now < deadline:
                    await asyncio.sleep(interval)
                    await message.channel.send(task + " - " + db[task]['User'])
                    now = datetime.now().astimezone(timezone_VN)
            elif type_content.startswith("remind me in"): 
                  interval = float(type_content.split()[-2])
                  interval_content = interval
                  time_type = type_content.split()[-1]

                  if time_type == 'minutes' or time_type == 'min':
                    interval = interval *60
                  elif time_type == 'hours':
                    interval = interval * 3600
                  elif time_type == 'days':
                    interval = interval * 3600*24
                  
                  if deadline < now:
                    await message.channel.send("`The deadline is already expired, please re-add the task`")
                  else:
                    await message.channel.send('`You will be reminded` ' + str(interval_content) + ' ' + time_type + ' `from now`')
                    await asyncio.sleep(interval)
                    await message.channel.send(task + " - " + db[task]['User'])
            elif type_content.startswith("remind me at"):
                  time_to_remind = type_content.split(' ',3)[-1]
                  pattern = '%d-%m-%Y %H:%M'     
                  time_to_remind = datetime.strptime(time_to_remind, pattern)
                  time_to_remind_aware = time_to_remind.replace(tzinfo=timezone.utc)

                  if time_to_remind_aware < now: 
                    await message.channel.send("`The time has already passed, please re-add the task`")
                  else:
                    await message.channel.send('`You will be reminded at` ' + str(time_to_remind))
                    while now < time_to_remind_aware:
                      now = datetime.now().astimezone(timezone_VN)
                    await message.channel.send(task + " - " + db[task]['User'])

            elif type_content.startswith("remind me") and type_content.endswith('before'):
                  interval = float(type_content.split()[2])
                  time_type = type_content.split()[-2]
                  time_to_

                  if time_type == 'minutes' or time_type == 'min':
                    time_to_remind == (deadline - timedelta(minute= interval)).date()
                  elif time_type == 'hours':
                    time_to_remind == (deadline - timedelta(minutes= (interval*60))).date()
                  elif time_type == 'days':
                    time_to_remind == (deadline - timedelta(days= (interval*60*24))).date()

                  if time_to_remind < now:
                    await message.channel.send("`The time is already expired, please re-add the task`")
                  else:
                    await message.channel.send('`You will be reminded` ' + str(interval) + time_type + ' `before the deadline`')
                    while now < time_to_remind:
                      now = datetime.now().astimezone(timezone_VN)
                    await message.channel.send(task + " - " + db[task]['User'])


      else:
        await message.channel.send("`Task doesn't exist. Please try again!`")
        return

    
    if msg.startswith('!taskdue'):
      '''THIS COMMAND IS TO SEE ALL THE TASKS THAT DUE ON A SPECIFIED DATE'''

      date_ = (msg.split('!taskdue ',1)[1])

      lst_task_date = {}
      today = datetime.today().astimezone(timezone_VN).date()
      today_weekday = today.weekday()

      if date_ == 'today':
        due_day = today
        
        for i in db:
          deadline = convert_deadline_db_to_date(i)
          
          if deadline == due_day:
            lst_task_date[i] = db[i]

      elif date_ == 'tomorrow':
        due_day = today + timedelta(days=1)
       
        for i in db:
          deadline = convert_deadline_db_to_date(i)
                    
          if deadline == due_day:
            lst_task_date[i] = db[i]

      elif date_ == 'this week':
        this_monday = today + timedelta(days=today_weekday)
        this_sunday = today + timedelta(days = 6) - timedelta(days=today_weekday) 
      
        for i in db:
          deadline = convert_deadline_db_to_date(i)

          if this_monday <= deadline <= this_sunday:
            lst_task_date[i] = db[i]

      elif date_ == 'next week':
        next_monday = today + timedelta(days = 7) - timedelta(days=today_weekday) 
        next_sunday = today + timedelta(days = 13) - timedelta(days=today_weekday)

        for i in db:
          deadline = convert_deadline_db_to_date(i)
                    
          if next_monday <= deadline <= next_sunday:
            lst_task_date[i] = db[i]

      elif date_ == 'this month':
        this_month = today.month
        this_year = today.year
      
        for i in db:
          deadline = convert_deadline_db_to_date(i)

          if this_month == deadline.month and this_year == deadline.year:
            lst_task_date[i] = db[i]

      elif date_ == 'next month':
        this_month = today.month
        next_month = today.month + 1
        this_year = today.year
        next_year = this_year + 1
    
        for i in db:
          deadline = convert_deadline_db_to_date(i)

          if (
              (next_month == deadline.month and this_year == deadline.year) or
              (this_month == 12 and deadline.month == 1 and next_year == deadline.year)
          ):
            lst_task_date[i] = db[i]

      else: 
        try:
          '''if the input is DD-MM-YYYY'''
          due_day = datetime.strptime(date_, '%d-%m-%Y').date()
          
          for i in db:
            deadline = convert_deadline_db_to_date(i)
            
            if due_day == deadline:
              lst_task_date[i] = db[i]
        except ValueError:
          try:
            '''if the input is DD-MM'''
            this_year = today.year
            due_day = datetime.strptime(date_ + str(this_year), '%d-%m%Y').date()
            
            for i in db:
              deadline = convert_deadline_db_to_date(i)

              if due_day == deadline:
                lst_task_date[i] = db[i]
          
          except ValueError:
            await message.channel.send('You inputted the wrong format, please try again. `?due` for more detail')
            return
            
      pretty_dic = make_pretty_dic(lst_task_date)
      embed = discord.Embed(title='Current task list due on ' + date_,description=pretty_dic,color=0xffc800)
      await message.channel.send(embed = embed)

    
    """Below are instructions that help user to know how to use bot"""

    if msg.startswith('?help'):
        '''THIS COMMAND PRINTS HOW TO USE BOT AND ITS FUNTIONS'''

        embed = discord.Embed(
          title = "Reminder Buddy: How-to  |  `?help`",
          description = "_This friend will help you to promptly set up your tasks with specified deadlines then friendly remind you of those tasks along the way!_",
          color=0x00b3ff
        )
        
        embed.add_field(name = ":alarm_clock: `!reminder`", value = "To set reminder for an existing task, following the format: `!reminder [taskname]`. Type `?reminder` for more details", inline = False)

        embed.add_field(name = ":page_facing_up: `!task`", value = "To see list of current tasks and deadlines", inline = False)
        
        embed.add_field(name = ":memo: `!add`", value = "To add a new task, following the format: `!add [taskname]`", inline = False)
        
        embed.add_field(name = ":speech_balloon: `!remove`", value = "To remove an existing task, following the format: `!remove [taskname]`", inline = False)

        embed.add_field(name = ":pushpin: `!howlong`", value = "To check deadline for an existing task, following the format: `!howlong [taskname]`", inline = False)

        embed.add_field(name = ":blue_book: `!taskuser`", value = "To see the task list of a specific user, following the format: `!taskuser [username]`", inline = False)

        embed.add_field(name = ":ledger: `!taskdue`", value = "To see all the tasks that are due on a specific date, following the format: `!taskdue [date]`. Type `?due` for more details", inline = False)


        await message.channel.send(embed = embed)

    
    if msg.startswith('?due'):
        '''THIS COMMAND PRINTS HOW TO USE THE COMMAND !taskdue'''

        embed = discord.Embed(
          title = "How to see all the tasks that are due on a certain date? |  `?due`",
          description = "Type `!taskdue` + the following keyword:",
          color=0x000000
        )
        
        embed.add_field(name = "`today`", value = "To get a list of tasks due **today**`", inline = False)

        embed.add_field(name = "`tomorrow`", value = "To get a list of tasks due **tomorrow**", inline = False)

        embed.add_field(name = "`this week`", value = "To get a list of tasks due **this week**", inline = False)

        embed.add_field(name = "`next week`", value = "To get a list of tasks due **next week**", inline = False)

        embed.add_field(name = "`this month`", value = "To get a list of tasks due **this month**", inline = False) 

        embed.add_field(name = "`next month`", value = "To get a list of tasks due **next month**", inline = False) 

        embed.add_field(name = "`DD-MM-YYYY`", value = "To get a list of tasks due on the specified date", inline = False) 

        embed.add_field(name = "`DD-MM`", value = "To get a list of tasks due on the specified date in the same year", inline = False) 

        await message.channel.send(embed = embed)

    
    if msg.startswith('?reminder'):
        '''THIS COMMAND PRINTS HOW TO USE THE COMMAND !reminder'''

        embed = discord.Embed(
          title = "How to set reminder? |  `?reminder`",
          description = "Enter `!reminder [taskname]` then choose a type of reminder to finish setting:",
          color=0x000000
        )
        
        embed.add_field(name = "`auto`", value = "To get reminded every 5 hours, type `auto`", inline = False)

        embed.add_field(name = "`custom`", value = "To set the interval for the reminder, type `custom`", inline = False)

        embed.add_field(name = "`remind me in`", value = "To get reminded in set time, type `remind me in n [days/hours/minutes]`", inline = False)

        embed.add_field(name = "`remind me at`", value = "To get reminded at a specific time, type `remind me at DD-MM-YYYY HH:MM`", inline = False)

        embed.add_field(name = "`remind me before`", value = "To get reminded before the deadline, type `remind me n [days/hours/minutes] before`", inline = False)

        await message.channel.send(embed = embed)

    await client.process_commands(message)
    

client.run('MTAyMDg1MDAzMzA1MjA5MDM5OA.Gfm_IP.FADklco1CjaIH-bYGcX2Gl01FGqMk6i9ME_7Mo')