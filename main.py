import TempleGuide
import sys

# TODO: how do you return a datastructure/plot that represents all the temples w/ 'Q' in the name built in 2000


def do_plots():
    while True:
        plot_type = input('Plot Type (empty string to stop): ')
        if plot_type == '':
            break
        elif plot_type == 'bar':
            # do something
            pass
        elif plot_type == 'map':
            # do something
            pass
        else:
            print('Only bar graphs ("bar") and maps ("map") are supported.')


def main():
    db = TempleGuide.Database()
    db.make_bar('y')
    args = sys.argv[1:]

    num_args = len(args)
    if num_args < 0 or num_args > 1:
        print('Please specify the action to take as first argument.')
        print('Add -s to search temples')
        print('Add -p to plot temples')
    else:
        if args[0] == '-s':
            pass
        if args[0] == '-p':
            do_plots()





if __name__ == '__main__':
    main()
