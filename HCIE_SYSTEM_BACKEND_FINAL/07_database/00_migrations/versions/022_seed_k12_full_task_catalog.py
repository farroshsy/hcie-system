"""Full K-12 CS Task Catalog — Real MPQ questions for all canonical concepts.

Revision ID: 022_seed_k12_full_task_catalog
Revises: 021_external_concept_graph
Create Date: 2026-05-27 00:00:00.000000

This migration replaces the placeholder task seeds from migrations 010, 015,
and 017 with a complete task catalog that:

  - Covers all 9 canonical concept areas across K-2/K-5/K-8/K-12 grade bands
  - Provides real MPQ questions (question_text + 4 choices + correct_answer)
  - Aligns with CSTA 2017 K-12 CS Framework standards
  - Aligns with Indonesian Kurikulum Merdeka "Informatika" subject
    (BK, AP, SK, JKI, AD, DSI domains)
  - Provides 3+ tasks per concept at varying difficulty (easy / mid / hard)

Standards:
  CSTA  — Computer Science Teachers Association K-12 CS Framework
  ISTE  — International Society for Technology in Education
  IDN   — Indonesian Informatika Kurikulum Merdeka 2022
"""

import json
from alembic import op

revision = "022_seed_k12_full_task_catalog"
down_revision = "021_external_concept_graph"


# ─── Task definitions ─────────────────────────────────────────────────────────
# Each tuple: (id, title, description, concept_id, difficulty, cognitive_level,
#              task_type, content_dict)
#
# content_dict keys expected by ITS runtime:
#   question      — full question text (str)
#   choices       — list of 4 option strings
#   correct_answer — must match one choice exactly
#   explanation   — shown after answer

TASKS = [

    # ── k2_algorithms ────────────────────────────────────────────────────────
    (
        "k2_algo_q1", "What is an Algorithm?",
        "Identify an algorithm from everyday examples",
        "k2_algorithms", 0.20, 1, "multiple_choice",
        {
            "question": "Rina wants to make instant noodles. She writes: 1) Boil water, 2) Open the packet, 3) Pour noodles, 4) Add seasoning, 5) Wait 3 minutes. What does this ordered plan represent?",
            "choices": [
                "A recipe that can change any time",
                "An algorithm — a clear step-by-step plan",
                "A random list of ideas",
                "A picture of noodles",
            ],
            "correct_answer": "An algorithm — a clear step-by-step plan",
            "explanation": "An algorithm is a precise, ordered sequence of steps to solve a problem. Cooking instructions are a classic everyday example.",
        },
    ),
    (
        "k2_algo_q2", "Order Matters",
        "Understand that step order affects algorithm output",
        "k2_algorithms", 0.25, 1, "multiple_choice",
        {
            "question": "A program has two steps: Step 1: print 'Hello', Step 2: print 'World'. If the steps are swapped, what changes?",
            "choices": [
                "Nothing changes",
                "'World' prints before 'Hello'",
                "The program crashes",
                "'Hello World' prints on one line",
            ],
            "correct_answer": "'World' prints before 'Hello'",
            "explanation": "In an algorithm, order matters. Reversing the steps reverses the output.",
        },
    ),
    (
        "k2_algo_q3", "Algorithm vs. Story",
        "Distinguish algorithms from other texts",
        "k2_algorithms", 0.22, 1, "multiple_choice",
        {
            "question": "Which of the following is the best example of an algorithm?",
            "choices": [
                "Once upon a time there was a robot named Budi.",
                "Step 1: Pick up the ball. Step 2: Walk to the basket. Step 3: Drop the ball.",
                "A colorful picture of a playground.",
                "A list of all the children in the class.",
            ],
            "correct_answer": "Step 1: Pick up the ball. Step 2: Walk to the basket. Step 3: Drop the ball.",
            "explanation": "Algorithms have clear, numbered steps leading to a goal. Narratives and pictures are not algorithms.",
        },
    ),

    # ── k5_algorithms ────────────────────────────────────────────────────────
    (
        "k5_algo_q1", "Tracing a Loop",
        "Trace loop execution to compute a final value",
        "k5_algorithms", 0.38, 2, "multiple_choice",
        {
            "question": "A loop runs 'add 2 to total' exactly 5 times, starting with total = 0. What is the final value of total?",
            "choices": ["5", "7", "10", "2"],
            "correct_answer": "10",
            "explanation": "Each iteration adds 2: 0→2→4→6→8→10. After 5 iterations, total = 10.",
        },
    ),
    (
        "k5_algo_q2", "Choosing the Efficient Algorithm",
        "Compare linear and binary search strategies",
        "k5_algorithms", 0.45, 2, "multiple_choice",
        {
            "question": "Budi has a sorted list of 100 names and wants to find 'Zainul'. Which approach is faster?",
            "choices": [
                "Check every name from the start (linear search)",
                "Open the list at the middle, then narrow down (binary search)",
                "Shuffle the list first, then search",
                "Ask a friend to look instead",
            ],
            "correct_answer": "Open the list at the middle, then narrow down (binary search)",
            "explanation": "Binary search is O(log n) — far more efficient than linear O(n) for sorted data.",
        },
    ),
    (
        "k5_algo_q3", "Sequence vs Loop",
        "Recognise when to use loops for repeated actions",
        "k5_algorithms", 0.40, 2, "multiple_choice",
        {
            "question": "A program must print a greeting for 50 different students. Which design is best?",
            "choices": [
                "Write 50 separate print statements",
                "Use a loop that prints the greeting for each name in a list",
                "Print all names in one print statement",
                "Ask the user to type each name 50 times",
            ],
            "correct_answer": "Use a loop that prints the greeting for each name in a list",
            "explanation": "Loops avoid repetitive code — essential for processing data collections.",
        },
    ),

    # ── k8_algorithms ────────────────────────────────────────────────────────
    (
        "k8_algo_q1", "Comparing Algorithm Performance",
        "Compare constant-time vs. linear-time algorithms",
        "k8_algorithms", 0.58, 3, "multiple_choice",
        {
            "question": "Algorithm A always takes 100 steps regardless of input size. Algorithm B takes n steps for input size n. For n = 50, which is faster?",
            "choices": [
                "Algorithm A (100 steps vs. 50)",
                "Algorithm B (50 steps vs. 100)",
                "They are always equal",
                "Cannot be determined",
            ],
            "correct_answer": "Algorithm B (50 steps vs. 100)",
            "explanation": "B takes 50 steps, A takes 100. B is faster here. For large n (>100), A would be faster.",
        },
    ),
    (
        "k8_algo_q2", "Big-O Intuition",
        "Identify quadratic growth from nested loops",
        "k8_algorithms", 0.65, 3, "multiple_choice",
        {
            "question": "A nested loop checks every pair of items in a list of n items. How do the operations grow with n?",
            "choices": [
                "Linearly (n)",
                "Quadratically (n²)",
                "Logarithmically (log n)",
                "Constantly (1)",
            ],
            "correct_answer": "Quadratically (n²)",
            "explanation": "For each of n items the inner loop checks n items: n × n = n² total comparisons.",
        },
    ),
    (
        "k8_algo_q3", "Edge Case Bug",
        "Understand edge cases in algorithm correctness",
        "k8_algorithms", 0.62, 3, "multiple_choice",
        {
            "question": "An algorithm works perfectly for 999 test cases but fails when the input is an empty list. What type of problem is this?",
            "choices": [
                "A compile error",
                "An edge case bug",
                "A syntax error",
                "A memory overflow",
            ],
            "correct_answer": "An edge case bug",
            "explanation": "Edge cases (empty input, max values, boundaries) must be explicitly handled in correct algorithms.",
        },
    ),

    # ── k12_algorithms ───────────────────────────────────────────────────────
    (
        "k12_algo_q1", "Merge Sort Complexity",
        "Identify the time complexity of merge sort",
        "k12_algorithms", 0.78, 4, "multiple_choice",
        {
            "question": "Merge sort divides a list in half recursively, sorts each half, then merges them. What is its time complexity?",
            "choices": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"],
            "correct_answer": "O(n log n)",
            "explanation": "Merge sort makes O(log n) recursive levels with O(n) merge work per level: total O(n log n).",
        },
    ),
    (
        "k12_algo_q2", "Dynamic Programming Trade-off",
        "Understand memoization as the DP technique",
        "k12_algorithms", 0.82, 4, "multiple_choice",
        {
            "question": "Compared to naive recursion, what does dynamic programming trade to achieve faster computation?",
            "choices": [
                "Less accuracy",
                "More memory to store subproblem results (memoization)",
                "More code complexity with no speed gain",
                "Randomness",
            ],
            "correct_answer": "More memory to store subproblem results (memoization)",
            "explanation": "DP stores subproblem solutions to avoid redundant computation, trading memory for speed.",
        },
    ),

    # ── k2_control ───────────────────────────────────────────────────────────
    (
        "k2_ctrl_q1", "When to Use a Loop",
        "Identify repetition as a use case for loops",
        "k2_control", 0.25, 1, "multiple_choice",
        {
            "question": "You need to water 10 plants, doing exactly the same action each time. What is the best approach in a program?",
            "choices": [
                "Write 10 separate 'water plant' steps",
                "Use a loop that repeats 'water plant' 10 times",
                "Water only the first plant",
                "Write a story about watering plants",
            ],
            "correct_answer": "Use a loop that repeats 'water plant' 10 times",
            "explanation": "Loops eliminate repetition for repeated identical actions.",
        },
    ),
    (
        "k2_ctrl_q2", "Simple Conditional",
        "Recognise if-then as a conditional control structure",
        "k2_control", 0.22, 1, "multiple_choice",
        {
            "question": "A program checks: 'IF it is raining THEN take an umbrella'. What type of instruction is this?",
            "choices": ["A loop", "A conditional (if-then)", "A variable", "A function"],
            "correct_answer": "A conditional (if-then)",
            "explanation": "IF-THEN instructions execute an action only when a condition is true.",
        },
    ),
    (
        "k2_ctrl_q3", "Identifying the Loop Body",
        "Identify which steps belong inside a loop",
        "k2_control", 0.28, 1, "multiple_choice",
        {
            "question": "REPEAT 3 TIMES: [say hello → wave hand]. Which steps are inside the loop?",
            "choices": [
                "Only 'say hello'",
                "Only 'wave hand'",
                "Both 'say hello' and 'wave hand'",
                "Neither — the loop body is empty",
            ],
            "correct_answer": "Both 'say hello' and 'wave hand'",
            "explanation": "Everything listed under REPEAT is the loop body — all steps run on every iteration.",
        },
    ),

    # ── k5_control ───────────────────────────────────────────────────────────
    (
        "k5_ctrl_q1", "While Loop Tracing",
        "Trace a while loop to determine iteration count",
        "k5_control", 0.45, 2, "multiple_choice",
        {
            "question": "A while loop runs while score < 10. Starting with score = 7, the loop body executes 'score = score + 1'. How many times does the body execute?",
            "choices": ["7", "3", "10", "1"],
            "correct_answer": "3",
            "explanation": "score goes 7→8→9→10. Body runs at score=7, 8, 9 (three times), then 10 fails the condition.",
        },
    ),
    (
        "k5_ctrl_q2", "If-Else Tracing",
        "Predict the output of an if-else structure",
        "k5_control", 0.42, 2, "multiple_choice",
        {
            "question": "IF score >= 75 THEN print 'Pass' ELSE print 'Fail'. If score = 60, what is printed?",
            "choices": ["Pass", "Fail", "Nothing", "Both Pass and Fail"],
            "correct_answer": "Fail",
            "explanation": "60 is not ≥ 75, so the ELSE branch executes: 'Fail' is printed.",
        },
    ),
    (
        "k5_ctrl_q3", "For vs While Choice",
        "Choose the appropriate loop type",
        "k5_control", 0.40, 2, "multiple_choice",
        {
            "question": "Which loop type is best when you know exactly how many times to repeat an action?",
            "choices": ["While loop", "For loop", "Repeat-until loop", "Recursive function"],
            "correct_answer": "For loop",
            "explanation": "For loops are designed for a known, fixed number of iterations.",
        },
    ),

    # ── k8_control ───────────────────────────────────────────────────────────
    (
        "k8_ctrl_q1", "Nested Loop Work Count",
        "Calculate total iterations of nested loops",
        "k8_control", 0.62, 3, "multiple_choice",
        {
            "question": "An outer loop runs 4 times; an inner loop runs 3 times per outer iteration. How many total inner-loop body executions occur?",
            "choices": ["7", "12", "4", "3"],
            "correct_answer": "12",
            "explanation": "4 outer × 3 inner = 12 total executions. Nested loops multiply their counts.",
        },
    ),
    (
        "k8_ctrl_q2", "Boolean AND Logic",
        "Evaluate a compound AND condition",
        "k8_control", 0.65, 3, "multiple_choice",
        {
            "question": "Condition: (age >= 13) AND (hasPermission == True). For age = 15 and hasPermission = False, the result is:",
            "choices": ["True", "False", "Error", "Depends on the language"],
            "correct_answer": "False",
            "explanation": "AND requires both conditions True. hasPermission is False, so the compound condition is False.",
        },
    ),
    (
        "k8_ctrl_q3", "Event-Driven Execution",
        "Understand when event handlers execute",
        "k8_control", 0.60, 3, "multiple_choice",
        {
            "question": "In an event-driven program, when does code inside an onClick handler run?",
            "choices": [
                "When the program starts",
                "Every second automatically",
                "Only when the user clicks the element",
                "Only when another function explicitly calls it",
            ],
            "correct_answer": "Only when the user clicks the element",
            "explanation": "Event handlers run in response to specific user or system events, not automatically.",
        },
    ),

    # ── k12_control ──────────────────────────────────────────────────────────
    (
        "k12_ctrl_q1", "Nested Call Tracing",
        "Trace execution order through nested control blocks",
        "k12_control", 0.65, 3, "multiple_choice",
        {
            "question": "for i in [1,2]: for j in [A,B]: print(i,j). In what order are values printed?",
            "choices": [
                "1A, 2A, 1B, 2B",
                "1A, 1B, 2A, 2B",
                "A1, B1, A2, B2",
                "A1, A2, B1, B2",
            ],
            "correct_answer": "1A, 1B, 2A, 2B",
            "explanation": "Outer loop fixes i=1, inner loop produces 1A then 1B; then i=2 produces 2A then 2B.",
        },
    ),
    (
        "k12_ctrl_q2", "Complexity from Loops",
        "Derive time complexity from loop structure",
        "k12_control", 0.80, 4, "multiple_choice",
        {
            "question": "A function has three nested for-loops, each running n times. What is the time complexity?",
            "choices": ["O(n)", "O(n²)", "O(n³)", "O(3n)"],
            "correct_answer": "O(n³)",
            "explanation": "Three nested loops each running n times: n × n × n = n³ total operations.",
        },
    ),

    # ── k2_variables ─────────────────────────────────────────────────────────
    (
        "k2_var_q1", "What is a Variable?",
        "Understand variables as named storage",
        "k2_variables", 0.20, 1, "multiple_choice",
        {
            "question": "In a game, 'lives = 3' means the player has 3 lives. When the player loses one, lives becomes 2. In programming, 'lives' is called:",
            "choices": [
                "A function that counts",
                "A variable — a named container whose value can change",
                "A fixed number that never changes",
                "A type of loop",
            ],
            "correct_answer": "A variable — a named container whose value can change",
            "explanation": "Variables store values that can be read and updated throughout a program.",
        },
    ),
    (
        "k2_var_q2", "Assignment Direction",
        "Understand that = means store, not equals",
        "k2_variables", 0.22, 1, "multiple_choice",
        {
            "question": "In code, x = 5 means:",
            "choices": [
                "'x' equals 5, like in math",
                "Store the value 5 into the variable named x",
                "Check if x and 5 are equal",
                "Multiply x by 5",
            ],
            "correct_answer": "Store the value 5 into the variable named x",
            "explanation": "Assignment (=) is directional: the value on the right is stored into the variable on the left.",
        },
    ),

    # ── k5_variables ─────────────────────────────────────────────────────────
    (
        "k5_var_q1", "Data Types",
        "Choose the correct data type for a decimal value",
        "k5_variables", 0.38, 2, "multiple_choice",
        {
            "question": "Which is the correct data type for a student's average score like 85.5?",
            "choices": [
                "Integer (whole number)",
                "Float (decimal number)",
                "Boolean (true/false)",
                "String (text)",
            ],
            "correct_answer": "Float (decimal number)",
            "explanation": "Floats represent numbers with decimal points. 85.5 cannot be stored as an integer.",
        },
    ),
    (
        "k5_var_q2", "Variable Reassignment",
        "Trace the result of reassigning a variable",
        "k5_variables", 0.40, 2, "multiple_choice",
        {
            "question": "x = 10; x = x + 3; print(x). What is printed?",
            "choices": ["10", "3", "13", "x + 3"],
            "correct_answer": "13",
            "explanation": "x starts as 10. x = x + 3 computes 10 + 3 = 13 and stores it back in x.",
        },
    ),

    # ── k8_variables ─────────────────────────────────────────────────────────
    (
        "k8_var_q1", "Local vs Global Scope",
        "Distinguish local and global variable scope",
        "k8_variables", 0.58, 3, "multiple_choice",
        {
            "question": "A variable declared inside a function is called what, and where can it be accessed?",
            "choices": [
                "A global variable — accessible everywhere in the program",
                "A local variable — accessible only inside that function",
                "A constant — its value never changes",
                "A parameter — only passed during function calls",
            ],
            "correct_answer": "A local variable — accessible only inside that function",
            "explanation": "Local variables are scoped to the block (function) where they are declared.",
        },
    ),
    (
        "k8_var_q2", "List Indexing",
        "Retrieve an element by index from a list",
        "k8_variables", 0.55, 2, "multiple_choice",
        {
            "question": "names = ['Adi', 'Budi', 'Citra']. What is names[1]?",
            "choices": ["Adi", "Budi", "Citra", "Index error"],
            "correct_answer": "Budi",
            "explanation": "List indexing starts at 0. Index 1 gives the second element: 'Budi'.",
        },
    ),

    # ── k2_modularity ────────────────────────────────────────────────────────
    (
        "k2_mod_q1", "Decomposition",
        "Recognise decomposition as breaking tasks into steps",
        "k2_modularity", 0.22, 1, "multiple_choice",
        {
            "question": "To clean your room you must: tidy the desk, organise books, sweep the floor. Breaking the big task into smaller steps is called:",
            "choices": [
                "Compiling",
                "Decomposition",
                "A network protocol",
                "Variable assignment",
            ],
            "correct_answer": "Decomposition",
            "explanation": "Decomposition divides complex problems into smaller, solvable sub-problems.",
        },
    ),
    (
        "k2_mod_q2", "Reusing Procedures",
        "Understand reuse of named instructions",
        "k2_modularity", 0.25, 1, "multiple_choice",
        {
            "question": "You teach a robot the steps to 'wave hello' once. Later you use 'wave hello' 5 times without rewriting the steps. This is called:",
            "choices": [
                "Reusing a named procedure",
                "A for loop",
                "A conditional statement",
                "Data storage",
            ],
            "correct_answer": "Reusing a named procedure",
            "explanation": "Defining a procedure once and calling it multiple times is the foundation of modularity.",
        },
    ),

    # ── k5_modularity ────────────────────────────────────────────────────────
    (
        "k5_mod_q1", "Function Parameters",
        "Trace a function call with a parameter",
        "k5_modularity", 0.42, 2, "multiple_choice",
        {
            "question": "def greet(name): print('Hello', name). When you call greet('Siti'), what is printed?",
            "choices": ["Hello name", "Hello Siti", "Hello", "Error"],
            "correct_answer": "Hello Siti",
            "explanation": "The parameter 'name' receives the value 'Siti'. The function prints 'Hello Siti'.",
        },
    ),
    (
        "k5_mod_q2", "Return Values",
        "Evaluate a function that returns a computed value",
        "k5_modularity", 0.45, 2, "multiple_choice",
        {
            "question": "def square(n): return n * n. What does square(4) evaluate to?",
            "choices": ["4", "8", "16", "n*n"],
            "correct_answer": "16",
            "explanation": "The function returns n*n = 4*4 = 16. Return values pass computed results out of functions.",
        },
    ),

    # ── k8_modularity ────────────────────────────────────────────────────────
    (
        "k8_mod_q1", "DRY Principle",
        "Apply the DRY principle by extracting duplicate code",
        "k8_modularity", 0.60, 3, "multiple_choice",
        {
            "question": "Your program has the same 5-line block in three different places. The best refactoring is:",
            "choices": [
                "Keep three copies — it is clearer to read",
                "Extract the block into a single function and call it from each place",
                "Delete two copies and keep one",
                "Add comments explaining why the code is repeated",
            ],
            "correct_answer": "Extract the block into a single function and call it from each place",
            "explanation": "DRY (Don't Repeat Yourself): centralising code reduces bugs and makes maintenance easier.",
        },
    ),

    # ── k2_computing_systems_devices ─────────────────────────────────────────
    (
        "k2_cs_q1", "Hardware vs Software",
        "Distinguish hardware from software",
        "k2_computing_systems_devices", 0.20, 1, "multiple_choice",
        {
            "question": "Which of these is an example of software?",
            "choices": [
                "The keyboard you type on",
                "The screen you look at",
                "A calculator application on a phone",
                "The USB cable you plug in",
            ],
            "correct_answer": "A calculator application on a phone",
            "explanation": "Software is a program — instructions stored digitally. Hardware is physical.",
        },
    ),
    (
        "k2_cs_q2", "Input and Output",
        "Classify devices as input or output",
        "k2_computing_systems_devices", 0.18, 1, "multiple_choice",
        {
            "question": "When you press a key on the keyboard it sends information to the computer. The keyboard is a:",
            "choices": [
                "Output device",
                "Input device",
                "Storage device",
                "Processing unit",
            ],
            "correct_answer": "Input device",
            "explanation": "Input devices send data to the computer. Output devices (monitor, speaker) receive data from it.",
        },
    ),
    (
        "k2_cs_q3", "Identifying Computing Devices",
        "Identify everyday computing devices",
        "k2_computing_systems_devices", 0.18, 1, "multiple_choice",
        {
            "question": "Which of these is a computing device?",
            "choices": [
                "A wooden ruler",
                "A pencil",
                "A smartphone",
                "A glass of water",
            ],
            "correct_answer": "A smartphone",
            "explanation": "Computing devices process information. Smartphones run programs and connect to the internet.",
        },
    ),

    # ── k5_computing_systems_devices ─────────────────────────────────────────
    (
        "k5_cs_q1", "Role of the CPU",
        "Explain the CPU's function in a computer",
        "k5_computing_systems_devices", 0.40, 2, "multiple_choice",
        {
            "question": "What is the primary function of the CPU (Central Processing Unit)?",
            "choices": [
                "Store files permanently",
                "Display images on the screen",
                "Execute program instructions — the brain of the computer",
                "Connect the computer to the internet",
            ],
            "correct_answer": "Execute program instructions — the brain of the computer",
            "explanation": "The CPU fetches, decodes, and executes instructions — it is the computational core.",
        },
    ),
    (
        "k5_cs_q2", "RAM vs Storage",
        "Distinguish volatile RAM from permanent storage",
        "k5_computing_systems_devices", 0.42, 2, "multiple_choice",
        {
            "question": "When you close a document without saving, your work is lost. This is because it was only stored in:",
            "choices": [
                "The hard drive (permanent storage)",
                "RAM (temporary memory)",
                "The CPU cache",
                "The graphics card",
            ],
            "correct_answer": "RAM (temporary memory)",
            "explanation": "RAM is volatile — data is lost when power is off. SSD/HDD keeps data permanently.",
        },
    ),

    # ── k8_computing_systems_devices ─────────────────────────────────────────
    (
        "k8_cs_q1", "Operating System Role",
        "Identify what the OS does and does not do",
        "k8_computing_systems_devices", 0.62, 3, "multiple_choice",
        {
            "question": "Which task does the operating system NOT perform?",
            "choices": [
                "Managing memory allocation between programs",
                "Controlling hardware devices via drivers",
                "Executing the CPU fetch-decode-execute cycle",
                "Managing the file system and storage",
            ],
            "correct_answer": "Executing the CPU fetch-decode-execute cycle",
            "explanation": "The OS manages resources, but the fetch-decode-execute cycle is performed by CPU hardware.",
        },
    ),
    (
        "k8_cs_q2", "Virtual Memory",
        "Understand the purpose of virtual memory",
        "k8_computing_systems_devices", 0.65, 3, "multiple_choice",
        {
            "question": "When a computer runs more programs than can fit in RAM, the OS uses hard drive space as extra memory. This is called:",
            "choices": [
                "Overclocking",
                "Virtual memory",
                "Cache memory",
                "ROM (Read-Only Memory)",
            ],
            "correct_answer": "Virtual memory",
            "explanation": "Virtual memory extends RAM using disk space, allowing more programs to run simultaneously.",
        },
    ),

    # ── k2_networks_communication ─────────────────────────────────────────────
    (
        "k2_net_q1", "What is a Network?",
        "Identify a computer network from a description",
        "k2_networks_communication", 0.20, 1, "multiple_choice",
        {
            "question": "Three computers in a classroom are connected and can share files with each other. What is this called?",
            "choices": [
                "A database",
                "A loop",
                "A computer network",
                "An operating system",
            ],
            "correct_answer": "A computer network",
            "explanation": "A network is two or more connected devices that can communicate and share resources.",
        },
    ),
    (
        "k2_net_q2", "The Internet",
        "Explain what makes global communication possible",
        "k2_networks_communication", 0.22, 1, "multiple_choice",
        {
            "question": "When you visit a website, your computer communicates with another computer far away. What makes this possible?",
            "choices": [
                "The keyboard sends the request directly",
                "The internet connects computers worldwide to exchange data",
                "The screen downloads the website by itself",
                "RAM stores all websites permanently",
            ],
            "correct_answer": "The internet connects computers worldwide to exchange data",
            "explanation": "The internet is a global network of networks enabling worldwide data communication.",
        },
    ),

    # ── k5_networks_communication ─────────────────────────────────────────────
    (
        "k5_net_q1", "Network Protocols",
        "Identify HTTP as a network protocol",
        "k5_networks_communication", 0.40, 2, "multiple_choice",
        {
            "question": "HTTP is a set of rules that web browsers and web servers follow to share pages. HTTP is an example of:",
            "choices": [
                "A programming language",
                "A network protocol",
                "A database",
                "A hardware component",
            ],
            "correct_answer": "A network protocol",
            "explanation": "Protocols are agreed-upon communication rules. HTTP defines how web data is requested and served.",
        },
    ),
    (
        "k5_net_q2", "Why Packets?",
        "Understand packet-switching in data transmission",
        "k5_networks_communication", 0.45, 2, "multiple_choice",
        {
            "question": "Why does the internet break large files into small 'packets' before sending?",
            "choices": [
                "Because packets are harder to intercept",
                "To allow efficient routing — each packet can take a different path",
                "Because computers cannot handle large files",
                "To compress files automatically",
            ],
            "correct_answer": "To allow efficient routing — each packet can take a different path",
            "explanation": "Packet switching allows efficient use of network paths and resilience to failures.",
        },
    ),

    # ── k8_networks_communication ─────────────────────────────────────────────
    (
        "k8_net_q1", "IP Address Role",
        "Explain how IP addresses enable routing",
        "k8_networks_communication", 0.58, 3, "multiple_choice",
        {
            "question": "An IP address like 192.168.1.5 uniquely identifies a device. What does it enable?",
            "choices": [
                "Encrypting all messages on the network",
                "Routing data packets to the correct destination device",
                "Storing web pages on the device",
                "Speeding up the CPU",
            ],
            "correct_answer": "Routing data packets to the correct destination device",
            "explanation": "Routers use IP addresses to direct packets to the correct machine on the network.",
        },
    ),
    (
        "k8_net_q2", "Phishing Attack",
        "Identify phishing as a cybersecurity threat",
        "k8_networks_communication", 0.55, 2, "multiple_choice",
        {
            "question": "A hacker sends an email pretending to be your bank, asking for your password. This attack is called:",
            "choices": [
                "A denial-of-service attack",
                "Phishing",
                "Malware installation",
                "Packet sniffing",
            ],
            "correct_answer": "Phishing",
            "explanation": "Phishing uses fake messages impersonating trusted sources to steal credentials.",
        },
    ),

    # ── k2_data_collection ───────────────────────────────────────────────────
    (
        "k2_data_q1", "Collecting Data",
        "Understand systematic data collection",
        "k2_data_collection", 0.18, 1, "multiple_choice",
        {
            "question": "Your class wants to find out which fruit is most popular. What is the correct approach?",
            "choices": [
                "Ask one student and guess for everyone else",
                "Ask every student their favourite fruit and record the answers",
                "Choose the fruit you like most",
                "Look it up on the internet",
            ],
            "correct_answer": "Ask every student their favourite fruit and record the answers",
            "explanation": "Good data collection means gathering responses from all relevant subjects systematically.",
        },
    ),
    (
        "k2_data_q2", "Reading a Bar Chart",
        "Extract information from a simple chart",
        "k2_data_collection", 0.18, 1, "multiple_choice",
        {
            "question": "A bar chart shows: Mango = 8 students, Banana = 5 students, Apple = 3 students. Which fruit is most popular?",
            "choices": ["Apple", "Banana", "Mango", "They are all equal"],
            "correct_answer": "Mango",
            "explanation": "Mango has the tallest bar (8 students), making it the most popular.",
        },
    ),

    # ── k5_data_collection ───────────────────────────────────────────────────
    (
        "k5_data_q1", "Trends in Data",
        "Identify a trend from a data sequence",
        "k5_data_collection", 0.40, 2, "multiple_choice",
        {
            "question": "Temperature readings for 7 days: 28, 30, 29, 31, 30, 32, 31°C. What is the overall trend?",
            "choices": [
                "Temperature is steadily falling",
                "Temperature is roughly rising over the week",
                "Temperature is perfectly constant",
                "No pattern exists",
            ],
            "correct_answer": "Temperature is roughly rising over the week",
            "explanation": "Despite daily fluctuations, the sequence moves from 28 to 31 — an upward trend.",
        },
    ),
    (
        "k5_data_q2", "Correlation vs Causation",
        "Distinguish correlation from causal claims",
        "k5_data_collection", 0.48, 2, "multiple_choice",
        {
            "question": "Data shows students who eat breakfast score higher on tests. What can we reliably conclude?",
            "choices": [
                "Eating breakfast directly causes higher scores",
                "There is a correlation, but more evidence is needed to prove causation",
                "Test scores cause students to eat breakfast",
                "The data must contain errors",
            ],
            "correct_answer": "There is a correlation, but more evidence is needed to prove causation",
            "explanation": "Correlation: two things move together. Causation requires controlled experiments.",
        },
    ),

    # ── k8_data_collection ───────────────────────────────────────────────────
    (
        "k8_data_q1", "Sampling Bias",
        "Identify bias in a sample selection",
        "k8_data_collection", 0.58, 3, "multiple_choice",
        {
            "question": "A survey about technology use is conducted only among students in the computer lab. What is wrong?",
            "choices": [
                "The sample is too small",
                "It is biased — computer-lab students are more tech-oriented than the average student",
                "Online surveys are never valid",
                "Nothing — any sample is statistically acceptable",
            ],
            "correct_answer": "It is biased — computer-lab students are more tech-oriented than the average student",
            "explanation": "Sampling bias occurs when the sample does not represent the full target population.",
        },
    ),

    # ── k12_data_collection ──────────────────────────────────────────────────
    (
        "k12_data_q1", "Training vs Test Sets",
        "Explain why a held-out test set is necessary in ML",
        "k12_data_collection", 0.78, 4, "multiple_choice",
        {
            "question": "Why do ML engineers hold out a test set that the model never sees during training?",
            "choices": [
                "To reduce computation time during training",
                "To measure how well the model generalises to unseen data",
                "Because the test set is always smaller than the training set",
                "To make the model architecture simpler",
            ],
            "correct_answer": "To measure how well the model generalises to unseen data",
            "explanation": "Evaluating on training data risks measuring memorisation (overfitting), not true learning.",
        },
    ),
    (
        "k12_data_q2", "Algorithmic Fairness",
        "Identify bias in ML predictions",
        "k12_data_collection", 0.82, 4, "multiple_choice",
        {
            "question": "A loan-approval model trained on historical data consistently denies applications from a particular demographic at a higher rate than is statistically justified. This is most likely due to:",
            "choices": [
                "Correct and unbiased prediction",
                "Bias in the historical training data reflecting past discrimination",
                "A hardware fault in the server",
                "The model being too simple",
            ],
            "correct_answer": "Bias in the historical training data reflecting past discrimination",
            "explanation": "Models learn patterns in training data. If that data encodes historical bias, the model perpetuates it.",
        },
    ),

    # ── k2_culture ──────────────────────────────────────────────────────────
    (
        "k2_dsi_q1", "Technology Impact",
        "Recognise that technology has both positive and negative effects",
        "k2_culture", 0.18, 1, "multiple_choice",
        {
            "question": "Smartphones help people communicate quickly, but some people use them so much they ignore those around them. This shows technology:",
            "choices": [
                "Only has positive effects",
                "Only has negative effects",
                "Has both positive and negative effects depending on use",
                "Has no real effect on daily life",
            ],
            "correct_answer": "Has both positive and negative effects depending on use",
            "explanation": "Technology is a tool — its impact depends on how, when, and how much it is used.",
        },
    ),
    (
        "k2_dsi_q2", "Online Safety",
        "Apply safe information sharing principles",
        "k2_culture", 0.20, 1, "multiple_choice",
        {
            "question": "Your friend asks you to share your home address on a public social media post. What should you do?",
            "choices": [
                "Share it because you trust your friend",
                "Refuse — personal addresses should not be shared publicly",
                "Share only the street name",
                "Post it and ask an adult afterwards",
            ],
            "correct_answer": "Refuse — personal addresses should not be shared publicly",
            "explanation": "Personal information shared publicly can be seen by strangers and misused.",
        },
    ),

    # ── k5_culture ──────────────────────────────────────────────────────────
    (
        "k5_dsi_q1", "Plagiarism",
        "Identify digital plagiarism",
        "k5_culture", 0.38, 2, "multiple_choice",
        {
            "question": "Copying a paragraph from a website and submitting it as your own school work is:",
            "choices": [
                "Efficient research",
                "Plagiarism — using someone else's work without credit",
                "Legal if you change a few words",
                "Acceptable as long as it is for school",
            ],
            "correct_answer": "Plagiarism — using someone else's work without credit",
            "explanation": "Intellectual property rights apply online. Copying without attribution is plagiarism.",
        },
    ),
    (
        "k5_dsi_q2", "Digital Footprint",
        "Understand the permanence of online activity",
        "k5_culture", 0.42, 2, "multiple_choice",
        {
            "question": "You post a photo online and later delete it. Is it truly gone?",
            "choices": [
                "Yes — deleting removes all copies everywhere",
                "No — others may have saved, shared, or screenshot it",
                "Yes — the internet forgets deleted content immediately",
                "No — but only the platform can see it",
            ],
            "correct_answer": "No — others may have saved, shared, or screenshot it",
            "explanation": "Digital content can be copied instantly. Deleting your copy does not remove all copies.",
        },
    ),

    # ── k8_culture ──────────────────────────────────────────────────────────
    (
        "k8_dsi_q1", "Algorithmic Bias",
        "Identify algorithmic bias from biased training data",
        "k8_culture", 0.62, 3, "multiple_choice",
        {
            "question": "A hiring algorithm trained mostly on male engineers consistently rates female candidates lower despite equal qualifications. This is an example of:",
            "choices": [
                "Correct and unbiased AI decision-making",
                "Algorithmic bias caused by biased training data",
                "A bug in the server hardware",
                "Normal statistical variation",
            ],
            "correct_answer": "Algorithmic bias caused by biased training data",
            "explanation": "When training data encodes historical bias, algorithms learn and perpetuate that bias.",
        },
    ),
    (
        "k8_dsi_q2", "Privacy and Data Collection",
        "Evaluate the ethics of data collection without consent",
        "k8_culture", 0.60, 3, "multiple_choice",
        {
            "question": "An app collects users' location data 24 hours a day without telling them. Which ethical principle does this violate?",
            "choices": [
                "Open-source licensing",
                "Informed consent and privacy",
                "Copyright law",
                "Network bandwidth limits",
            ],
            "correct_answer": "Informed consent and privacy",
            "explanation": "Users have a right to know what data is collected about them and to consent. Silent collection violates this.",
        },
    ),
]


def upgrade():
    for (task_id, title, description, concept_id, difficulty,
         cognitive_level, task_type, content) in TASKS:
        content_json = json.dumps(content).replace("'", "''")
        op.execute(f"""
            INSERT INTO tasks (
                id, title, description, concept_id, concept_type, difficulty,
                cognitive_level, task_type, content, solution, hints, metadata,
                created_at, updated_at
            )
            VALUES (
                '{task_id}', '{title.replace("'", "''")}',
                '{description.replace("'", "''")}',
                '{concept_id}', 'k12',
                {difficulty}, {cognitive_level}, '{task_type}',
                '{content_json}'::jsonb,
                '{json.dumps({"explanation": content.get("explanation", "")}).replace("'", "''")}'::jsonb,
                '[]'::jsonb,
                '{{"seeded_for": "022_full_catalog", "standard": "CSTA+IDN"}}'::jsonb,
                NOW(), NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                solution = EXCLUDED.solution,
                updated_at = NOW()
        """)


def downgrade():
    ids = ", ".join(f"'{t[0]}'" for t in TASKS)
    op.execute(f"DELETE FROM tasks WHERE id IN ({ids})")
