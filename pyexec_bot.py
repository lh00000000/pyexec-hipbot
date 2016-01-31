import hypchat
import signal
import time
import logging
import subprocess


logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)

bot_name = '/pyexec'
room_name = 'YOUR_ROOM_NAME'
api_key = 'YOUR_APIV2_KEY'


def timeout(a, b):
    raise RuntimeError


def subprocess_exec(src):

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(10)

    try:
        logging.debug('attempting to run %s' % src)
        cmd = 'python -c \'%s\'' % src.replace("\'", "\"")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()

        if out:
            result = out
        if err:
            result = err

    except SyntaxError as e:
        logging.debug('SyntaxError')

        result += str(e)
    except RuntimeError:
        logging.debug('ran too long')
        result += "Ran too long"

    signal.alarm(0)
    return result


def get_room(name, all_rooms):
    for room in all_rooms:
        if room['name'] == name:
            return room


def eval_bot_mentions(all_messages):
    for message in all_messages:
        message_text = message['message']
        if message_text.startswith(bot_name + ' '):
            logging.debug(message)
            text = message_text.replace(bot_name + ' ', '').strip()
            yield message['from']['mention_name'], text

if __name__ == "__main__":
    hc = hypchat.HypChat(api_key)
    logging.debug('connected to hipchat')

    all_rooms = hc.rooms(max_results=1000)['items']
    target_room = get_room(room_name, all_rooms)
    logging.debug('located %s Lounge room' % (room_name))

    after_message_id = target_room.latest(maxResults=1)['items'][0]['id']
    logging.debug('starting from id %s' % after_message_id)

    while True:
        try:
            logging.debug('fetching new messages')
            new_messages = target_room.latest(
                not_before=after_message_id)['items']
        except hypchat.requests.HttpServiceUnavailable:
            time.sleep(15)
            continue

        after_message_id = new_messages[-1]['id']
        for partner, text in eval_bot_mentions(new_messages[1:]):
            out = subprocess_exec("%s" % text)
            if out:
                logging.debug('trying to send %s/%s/%s' % (partner, text, out))

                target_room.message("@%s>>> %s\n%s" % (partner, text, out))
        time.sleep(5)
