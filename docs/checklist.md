# 8-point build standard

Run this before any AI phone agent takes real calls. Every point has a pass condition. If one fails, fix the prompt, then rerun that test.

## 1. Test inbound

Call the agent from your own phone, three times.

- Pass: it uses the inbound greeting, asks why you called, and never starts with the outbound line.

## 2. Test outbound

Trigger an outbound call to your own phone.

- Pass: it uses the outbound greeting, says who it is and why it is calling in one sentence, and asks if now is a good time.

## 3. Voicemail test

Send the outbound call to voicemail, and call from a phone with call screening turned on.

- Pass: on voicemail it leaves one short message and hangs up. It never says "are you still there" to the machine. With screening, it gives its name and business.

## 4. Opt-out test

Say "stop calling me" in the middle of a call.

- Pass: it confirms once, says it will take you off the list, and ends the call. It does not try to keep you on. The contact is marked do not call in your CRM.

## 5. Booking with time zone test

Book a time while pretending to be in a different time zone from the calendar.

- Pass: it asks your city, says both times, books only inside business hours in your time, and reads back name, number, email and time before booking. The event shows up on the calendar at the right hour.

## 6. Transfer test

Ask for a person, then ask again after hours.

- Pass: during hours it says who it is transferring you to and why, then transfers. After hours it takes a message instead. If the transfer fails, it says so and takes a message.

## 7. Idle reminder at 8 seconds, not 4

Stay silent on a live call and time how long it takes the agent to prompt you.

- Pass: the first reminder comes at about 8 seconds. At 4 seconds it cuts people off while they think or look something up. Keep the reminder short and never use it on a voicemail.

## 8. Review the first 20 real calls

Listen to the first 20 real calls, or read the transcripts, before you scale up.

- Look for: invented prices or facts, double questions, long speeches, wrong time zones, actions claimed that the tool never confirmed, and callers who got stuck.
- Pass: no invented facts, no false confirmations, and every failure has a prompt fix you have tested.

## After launch

Run `python lint_prompt.py your_prompt.md` every time you edit the prompt. Keep the score at 100 and the length under the limit.
