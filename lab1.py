from time import sleep
from redis import Redis, WatchError
from threading import Thread
from random import sample
from collections import Counter

UPCOMING_TICKET_ID = 'upcoming_ticket_id'

VALID_NUMBERS = list(range(1, 41))

def get_winner_tickets(connection: Redis):
    while True:
        try:
            number_of_winner_numbers = int(input('Enter how many numbers to roll: '))
            break
        except ValueError:
            print('Invalid input. Please enter a number.')

    winner_numbers = sample(VALID_NUMBERS, number_of_winner_numbers)
    winner_numbers.sort()
    print(f'Winner numbers: {winner_numbers}')

    with connection.pipeline() as pipe:
        for number in winner_numbers:
            pipe.watch(number)
        pipe.multi()
        for number in winner_numbers:
            if connection.llen(number) > 0:
                pipe.lrange(number, 0, -1)
        try:
            results = pipe.execute()
            winner_ticket_ids = [int(ticket_id) for sublist in results for ticket_id in sublist]
            print(f'Matching numbers of each winning ticket: {dict(Counter(winner_ticket_ids))}')
        except WatchError:
            print('An error occurred while getting winner tickets. Try again.')

def insert_ticket(ticket_id: int, ticket_numbers: list, connection: Redis):
    with connection.pipeline() as pipe:
        pipe.multi()
        for number in ticket_numbers:
            pipe.rpush(number, ticket_id)
        pipe.execute()

def draw_ticket_naive(connection: Redis):
    ticket_numbers = sample(VALID_NUMBERS, 5)
    ticket_numbers.sort()

    connection.watch(UPCOMING_TICKET_ID)
    ticket_id = int(connection.get(UPCOMING_TICKET_ID))
    connection.incr(UPCOMING_TICKET_ID)
    insert_ticket(ticket_id, ticket_numbers, connection)
    connection.unwatch()
    print(f'Ticket #{ticket_id} numbers: {ticket_numbers}')

def draw_ticket_slow(connection: Redis):
    with connection.pipeline() as pipe:
        ticket_numbers = sample(VALID_NUMBERS, 5)
        ticket_numbers.sort()

        pipe.watch(UPCOMING_TICKET_ID)
        pipe.multi()
        ticket_id = int(connection.get(UPCOMING_TICKET_ID))
        sleep(1)
        pipe.incr(UPCOMING_TICKET_ID)
        insert_ticket(ticket_id, ticket_numbers, connection)

        try:
            pipe.execute()
            print(f'Ticket #{ticket_id} numbers: {ticket_numbers}')
        except WatchError:
            print('Another ticket is being updated at the moment. Try drawing again.')

def draw_three_tickets(connection: Redis):
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

def upcoming_ticket_id(connection: Redis):
    upcoming_ticket_id = int(connection.get(UPCOMING_TICKET_ID))
    print(f'Upcoming ticket #{upcoming_ticket_id}')

def print_help():
    print('''
    ____________________________________________________________

    slow        - Draw a ticket using a slow method
    naive       - Draw a ticket using a naive method
    three       - Draw three tickets in three threads
    next        - Show the upcoming ticket id
    winners     - Start the lottery and get the winner tickets
    help        - Show this help
    exit        - Exit the program
    ____________________________________________________________

    ''')

processes = {
    'slow': lambda connection: draw_ticket_slow(connection),
    'naive': lambda connection: draw_ticket_naive(connection),
    'three': lambda connection: draw_three_tickets(connection),
    'next': lambda connection: upcoming_ticket_id(connection),
    'winners': lambda connection: get_winner_tickets(connection),
    'help': lambda _: print_help(),
    'exit': lambda _: exit()
}

def main():
    connection = Redis(host='localhost', port=6379, db=0)

    # Initialize current ticket id
    if not connection.exists(UPCOMING_TICKET_ID):
        connection.set(UPCOMING_TICKET_ID, 1)

    print('\nWelcome to the lottery!')
    print_help()

    while True:
        try:
            command = input('Enter a command: ')
            processes[command](connection)
        except KeyError:
            print('Invalid command. Enter "help" to see available commands.')

if __name__ == '__main__':
    main()
