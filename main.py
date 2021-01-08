import TempleGuide
import time


def main():
    db = TempleGuide.Database()


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
