from time import sleep
from redis import Redis, WatchError
from threading import Thread
from random import sample
from collections import Counter

CURRENT_TICKET_ID = 'current_ticket_id'

VALID_NUMBERS = list(range(1, 41))

def find_winner_tickets(winner_numbers: list, connection: Redis):
    winner_ticket_ids = []
    with connection.pipeline() as pipe:
        for number in winner_numbers:
            pipe.watch(number)
        pipe.multi()
        for number in winner_numbers:
            winner_ticket_ids += pipe.get(number)
        try:
            pipe.execute()
            # Counts the number of matching numbers in each ticket
            print(Counter(winner_ticket_ids))
        except WatchError:
            pipe.discard()
            print('Another ticket is being updated at the moment. Try drawing again.')
            return None

def insert_ticket(ticket_id: int, ticket_numbers: list, connection: Redis):
    with connection.pipeline() as pipe:
        for number in ticket_numbers:
            pipe.watch(number)
        for number in ticket_numbers:
            pipe.append(number, ticket_id)

def draw_ticket_naive(connection: Redis):
    connection.watch(CURRENT_TICKET_ID)
    ticket_id = int(connection.get(CURRENT_TICKET_ID))
    connection.incr(CURRENT_TICKET_ID)

    ticket_numbers = sample(VALID_NUMBERS, 5)
    ticket_numbers.sort()
    insert_ticket(ticket_id, ticket_numbers, connection)
    connection.unwatch()
    print(f'Ticket #{ticket_id} numbers: {ticket_numbers}')

    return ticket_id

def draw_ticket_slow(connection: Redis):
    with connection.pipeline() as pipe:
        pipe.watch(CURRENT_TICKET_ID)
        pipe.multi()
        ticket_id = int(connection.get(CURRENT_TICKET_ID))
        sleep(1)
        pipe.incr(CURRENT_TICKET_ID)

        ticket_numbers = sample(VALID_NUMBERS, 5)
        ticket_numbers.sort()
        insert_ticket(ticket_id, ticket_numbers, connection)
        try:
            pipe.execute()
            print(f'Ticket #{ticket_id} numbers: {ticket_numbers}')
            return ticket_id
        except WatchError:
            pipe.discard()
            print('Another ticket is being updated at the moment. Try drawing again.')
            return None

def main():
    connection = Redis(host='localhost', port=6379, db=0)
    connection.set(CURRENT_TICKET_ID, 1)

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

    upcoming_ticket_id = int(connection.get(CURRENT_TICKET_ID))
    print(f'Upcoming ticket #{upcoming_ticket_id}')

    # Draw winner tickets
    winner_numbers = sample(VALID_NUMBERS, 10)
    winner_numbers.sort()
    print(f'Winner numbers: {winner_numbers}')
    find_winner_tickets(winner_numbers, connection)

if __name__ == '__main__':
    main()
