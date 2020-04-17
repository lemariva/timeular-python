from functools import wraps

def check_bluetooth(f):
    """
    The decorator which checks for an active Bluetooth connection.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if args[0].zei:
            try:
                f(*args,**kwargs)
            except:
                args[0].the_connection_was_lost()
        else:
            args[0].display_message_box('showerror', 'No Connection',
                'You need to have an active Bluetooth connection first.')
    return wrapper