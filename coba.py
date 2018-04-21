import csv

fieldnames  = ['time','count']
filelog     = 'report.csv'

def reset():
    with open(filelog, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

def write(time, count):
    with open(filelog, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({fieldnames[0]: time, fieldnames[1]: count})

if __name__ == '__main__':
    reset()
    write('1', '2')
