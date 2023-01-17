# magical energy to deliver food
# special star fav snack
# 50 stars by end of december

# ownerproof-2694095-1670269374-9c25f2b7b465

def read_calories(file_name):
    with open(file_name, 'r', encoding="utf-8") as f:
        lines = f.readlines()

        max_calories = 0
        calories = 0 
        elf_counter = 0

        for line in lines:
            if line.strip():
                print('The line is NOT empty ->', line)
                calories += int(line)
                if max_calories <= calories:
                    max_calories = calories
                else: 
                    pass
            else:
                print('The line is empty')
                calories = 0
                elf_counter += 1
            
        return max_calories, elf_counter

def read_all_calories(file_name):
    with open(file_name, 'r', encoding="utf-8") as f:
        lines = f.readlines()
        calories = 0 
        elf_counter = 0

        calory_list = []

        for line in lines:
            if line.strip():
                print('The line is NOT empty ->', line)
                calories += int(line)
            else:
                print('The line is empty')
                calory_list.append(calories)
                calories = 0
                elf_counter += 1
        calory_list.sort()
        max_calories = calory_list[len(calory_list)-1]
        max_calories_2 = calory_list[len(calory_list)-2]
        max_calories_3 = calory_list[len(calory_list)-3]
        return max_calories + max_calories_2 + max_calories_3

if __name__ == "__main__":
    max_calories, elf = read_calories('01_input.txt')
    print(max_calories, elf)

    sum = read_all_calories('01_input.txt')
    print(sum)