import time

class FutureActions():

    def __init__(self):

        # list of functions to do in the future
        self.future_functions = []
        
        # list of times since function was added
        self.elapsed_time = []

    def add_function(self, time_to_wait, function, *args):
        self.future_functions.append([function, args])
        self.elapsed_time.append([time.time(),time_to_wait/1000])

    def do_if_time_elapsed_and_remove(self):
        items_to_remove = []
        for i in range(len(self.elapsed_time)):
            time_added = self.elapsed_time[i][0]
            time_to_wait = self.elapsed_time[i][1]
            if time.time() - time_added >= time_to_wait:
                function = self.future_functions[i][0]
                args = self.future_functions[i][1]
                function(*args)
                items_to_remove.append(i)

        self.remove_functions(items_to_remove)

    def remove_functions(self, items_to_remove):
        offset = 0
        for i in items_to_remove:
            item = i - offset
            del(self.future_functions[item])
            del(self.elapsed_time[item])
            offset += 1

if __name__ == "__main__":
    # example usage
    future_manager = FutureActions()

    def print_two(a,b):
        print(a + b)

    future_manager.add_function(2000,print,"hello world 2 seconds")
    future_manager.add_function(3000,print_two,"hello world 3 seconds", " plus more")

    while True:
        future_manager.do_if_time_elapsed_and_remove()

    
            
                
                
            
        
        
