from time import sleep
from redis import Redis, WatchError
from threading import Thread
from random import sample

TICKET_NUM_KEY = 'ticket_num'

VALID_NUMBERS = list(range(1, 41))

def draw_ticket_naive(connection: Redis):
    connection.watch(TICKET_NUM_KEY)
    ticket_num = int(connection.get(TICKET_NUM_KEY))
    connection.incr(TICKET_NUM_KEY)
    connection.unwatch()
    print(f'Drew ticket #{ticket_num}')

    ticket_numbers = sample(VALID_NUMBERS, 5)
    ticket_numbers.sort()
    print(f'Ticket #{ticket_num} numbers: {ticket_numbers}')
    # We can store the ticket_numbers as key and a list of tickets as value (?)

    return ticket_num

def draw_ticket_slow(connection: Redis):
    with connection.pipeline() as pipe:
        pipe.watch(TICKET_NUM_KEY)
        pipe.multi()
        ticket_num = int(connection.get(TICKET_NUM_KEY))
        sleep(1)
        pipe.incr(TICKET_NUM_KEY)
        try:
            pipe.execute()
        except WatchError:
            print('Another ticket is being updated at the moment. Try drawing again.')
            return None

    print(f'Drew ticket #{ticket_num}')

    ticket_numbers = sample(VALID_NUMBERS, 5)
    ticket_numbers.sort()
    print(f'Ticket #{ticket_num} numbers: {ticket_numbers}')

    return ticket_num

def main():
    connection = Redis(host='localhost', port=6379, db=0)
    connection.set(TICKET_NUM_KEY, 1)

    # Draw tickets in different threads
    draw_threads = [
        Thread(target=draw_ticket_naive, args=(connection,)),
        Thread(target=draw_ticket_slow, args=(connection,)),
        Thread(target=draw_ticket_naive, args=(connection,)),
    ]

    # Start draws
    for thread in draw_threads:
        thread.start()

    # Wait for draws to finish
    for thread in draw_threads:
        thread.join()


    upcoming_ticket = int(connection.get(TICKET_NUM_KEY))
    print(f'Upcoming ticket #{upcoming_ticket}')

if __name__ == '__main__':
    main()
