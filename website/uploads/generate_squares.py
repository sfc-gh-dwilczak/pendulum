# This script generates and prints the first 10 square numbers

def generate_squares(n):
    return [i ** 2 for i in range(1, n + 1)]

if __name__ == "__main__":
    squares = generate_squares(10)
    for square in squares:
        print(square)
