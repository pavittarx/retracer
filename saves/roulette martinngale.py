import random

balance = 2000  # Starting balance
initial_bet = 1  # Initial bet amount
num_tests = 100  # Number of tests

def calculate_safe_bet(balance, max_bet):
    # Calculate a safe bet amount based on the balance and maximum bet limit
    safe_bet = min(balance, max_bet)
    return safe_bet

def simulate_roulette():
    global balance
    
    # Reset balance and bet for each test
    initial_balance = balance
    bet_red = initial_bet
    bet_black = initial_bet
    red_loss_count = 0
    black_loss_count = 0
    zero_count = 0
    history = []  # List to store the history of bets, outcomes, and balances
    
    for _ in range(num_tests):
        # Simulate the roulette wheel by generating a random number between 0 and 36
        result = random.randint(0, 36)
        
        if result == 0:
            outcome = "zero"
            zero_count += 1
        else:
            # Determine if the number is red or black based on the result
            outcome = "red" if result % 2 == 0 and result != 0 else "black"
            zero_count = 0
        
        # Store the current bet, outcome, and balance in the history
        history.append((bet_red, bet_black, outcome, balance))
        
        # Check if the bets win or lose
        if result == 0:
            balance -= bet_red + bet_black  # Lose both red and black bets
            red_loss_count += 1
            black_loss_count += 1
            bet_red = calculate_safe_bet(balance, bet_red * 2)  # Adjust the red bet using a safe bet calculation
            bet_black = calculate_safe_bet(balance, bet_black * 2)  # Adjust the black bet using a safe bet calculation
        elif result % 2 == 0:
            balance += bet_red  # Win the red bet
            balance -= bet_black  # Lose the black bet
            red_loss_count = 0  # Reset the red loss count
            black_loss_count += 1
            bet_red = initial_bet  # Reset the red bet to the initial amount
            bet_black = calculate_safe_bet(balance, bet_black * 2)  # Adjust the black bet using a safe bet calculation
        else:
            balance -= bet_red  # Lose the red bet
            balance += bet_black  # Win the black bet
            red_loss_count += 1
            black_loss_count = 0  # Reset the black loss count
            bet_red = calculate_safe_bet(balance, bet_red * 2)  # Adjust the red bet using a safe bet calculation
            bet_black = initial_bet  # Reset the black bet to the initial amount
        
        # Hedge the opposite bet if one side loses 4 times consecutively (including zero outcomes)
        if red_loss_count >= 4 and zero_count < 4:
            bet_black = (bet_red + 1) // 2  # Hedge the opposite bet with (n+1)/2 on black
        elif black_loss_count >= 4 and zero_count < 4:
            bet_red = (bet_black + 1) // 2  # Hedge the opposite bet with (n+1)/2 on red
        
        # Stop if the balance reaches zero or goes to half of its initial value
        if balance <= 0 or balance <= 0.5 * initial_balance:
            break
    
    return history

history = simulate_roulette()

# Print the history of bets, outcomes, and balances
for i, (bet_red, bet_black, outcome, balance) in enumerate(history):
    print(f"Round {i+1}: Red bet: {bet_red}, Black bet: {bet_black}, Outcome: {outcome}, Balance: {balance}")


print("Final balance after " , num_tests, "tests:", balance )
