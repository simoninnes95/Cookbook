# You are given an array (which will have a length of at least 3, but could be very large) containing integers. 
# The array is either entirely comprised of odd integers or entirely comprised of even integers except for a single integer N. 
# Write a method that takes the array as an argument and returns this "outlier" N.
# Examples

# [2, 4, 0, 100, 4, 11, 2602, 36]
# Should return: 11 (the only odd number)

# [160, 3, 1719, 19, 11, 13, -21]
# Should return: 160 (the only even number)

# def find_outlier(integers):
#     list_count = len(integers)
#     odd_count = []
#     even_count = []

#     for item in integers:
#         if item % 2 == 0:
#             even_count.append(item)
#         else:
#             odd_count.append(item)

#     if len(odd_count) == 1:
#         output = odd_count[0]
#     else:
#         output = even_count[0]
#     return output

# integers = [160, 3, 1719, 19, 11, 13, -21]

# output = find_outlier(integers)
# print(output)

# def find_outlier(int):
#     odds = [x for x in int if x%2!=0]
#     evens= [x for x in int if x%2==0]
#     return odds[0] if len(odds)<len(evens) else evens[0]

# Backwards Read Primes are primes that when read backwards in base 10 (from right to left) are a different prime. (This rules out primes which are palindromes.)

# Examples:
# 13 17 31 37 71 73 are Backwards Read Primes

# 13 is such because it's prime and read from right to left writes 31 which is prime too. Same for the others.
# Task

# Find all Backwards Read Primes between two positive given numbers (both inclusive), the second one always being greater than or equal to the first one. 
# The resulting array or the resulting string will be ordered following the natural order of the prime numbers.
# Examples (in general form):

# backwardsPrime(2, 100) => [13, 17, 31, 37, 71, 73, 79, 97] backwardsPrime(9900, 10000) => [9923, 9931, 9941, 9967] backwardsPrime(501, 599) => []

# See "Sample Tests" for your language.

# num = 1234
# reversed_num = 0

# while num != 0:
#     digit = num % 10
#     reversed_num = reversed_num * 10 + digit
#     num //= 10

def backwards_prime(start, stop):
    check_list = [str(item) for item in range(start, stop+1)]
    reversed_list = [int(item[::-1]) if int(item) > 10 else int(item) for item in check_list ]
    output = []

    for num in reversed_list:
        if min(num%3,num%2,num%5) == 0: 
            pass
        elif min(num//3,num//2,num//5) == 0: 
            output.append(num)
        else: 
            output.append(num)
    return output

print(backwards_prime(2,100))


# def isPrime(n) :
#     if (n <= 1) :
#         return False
#     if (n <= 3) :
#         return True
#     if (n % 2 == 0 or n % 3 == 0) :
#         return False
#     i = 5
#     while(i * i <= n) :
#         if (n % i == 0 or n % (i + 2) == 0) :
#             return False
#         i = i + 6
#         return True


# def isprime(num):
#   if min(num%3,num%2,num%5) == 0: 
#     return False
#   elif min(num//3,num//2,num//5) == 0: 
#     return True
#   else: 
#     return True