from collections import Counter
from random import sample
from threading import Thread
from time import sleep

from redis import Redis, WatchError

UPCOMING_TICKET_ID = 'upcoming_ticket_id'
NAMES = 'names'

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
            matching_numbers = dict(Counter(winner_ticket_ids))

            print(f'Matching numbers of each winning ticket:')
            names = connection.smembers(NAMES)
            for ticket_id, count in matching_numbers.items():
                for name in names:
                    if connection.sismember(name, ticket_id):
                        winner_name = name.decode('utf-8')
                        break
                print(f"Ticket #{ticket_id} ({winner_name}) - {count} matching numbers")
        except WatchError:
            print('An error occurred while getting winner tickets. Try again.')

def insert_ticket(ticket_id: int, ticket_numbers: list, name: str, connection: Redis):
    for number in ticket_numbers:
        connection.rpush(number, ticket_id)
    connection.sadd(name, ticket_id)

def draw_ticket_naive(connection: Redis, name: str):
    ticket_numbers = sample(VALID_NUMBERS, 5)
    ticket_numbers.sort()

    ticket_id = int(connection.get(UPCOMING_TICKET_ID))
    connection.incr(UPCOMING_TICKET_ID)
    insert_ticket(ticket_id, ticket_numbers, name, connection)
    print(f'Ticket #{ticket_id} numbers: {ticket_numbers}')

def draw_ticket_slow(connection: Redis, name: str):
    with connection.pipeline() as pipe:
        ticket_numbers = sample(VALID_NUMBERS, 5)
        ticket_numbers.sort()

        pipe.watch(UPCOMING_TICKET_ID)
        pipe.watch(name)
        pipe.multi()
        ticket_id = int(connection.get(UPCOMING_TICKET_ID))
        sleep(1)
        pipe.incr(UPCOMING_TICKET_ID)
        insert_ticket(ticket_id, ticket_numbers, name, pipe)

        try:
            pipe.execute()
            print(f'Ticket #{ticket_id} numbers: {ticket_numbers}')
        except WatchError:
            print('Another ticket is being updated at the moment. Try drawing again.')

def draw_three_tickets(connection: Redis, name):
    draw_threads = [
        Thread(target=draw_ticket_naive, args=(connection, name)),
        Thread(target=draw_ticket_slow, args=(connection, name)),
        Thread(target=draw_ticket_naive, args=(connection, name)),
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
    'slow': lambda connection, name: draw_ticket_slow(connection, name),
    'naive': lambda connection, name: draw_ticket_naive(connection, name),
    'three': lambda connection, name: draw_three_tickets(connection, name),
    'next': lambda connection, _: upcoming_ticket_id(connection),
    'winners': lambda connection, _: get_winner_tickets(connection),
    'help': lambda _, __: print_help(),
    'exit': lambda _, __: exit()
}

def main():
    connection = Redis(host='localhost', port=6379, db=0)

    # Initialize current ticket id
    if not connection.exists(UPCOMING_TICKET_ID):
        connection.set(UPCOMING_TICKET_ID, 1)

    print('\nWelcome to the lottery!')

    name = input('Enter your name: ')
    connection.sadd(NAMES, name)
    print_help()

    while True:
        try:
            command = input('Enter a command: ')
            processes[command](connection, name)
        except KeyError:
            print('Invalid command. Enter "help" to see available commands.')

if __name__ == '__main__':
    main()
