"""
Task Registry - Handcrafted learning tasks that bind TO concepts.

Tasks should NOT exist independently - they bind to concepts.
This operationalizes: concept → measurable cognition

Each task is handcrafted for:
- Interpretability
- Debugging
- Replay clarity
- Educational validity
"""

from core.curriculum.concept_registry import (
    ConceptRegistry,
    LearningTask,
    TaskType,
    get_registry,
    initialize_intro_python_curriculum
)


def initialize_handcrafted_tasks():
    """
    Initialize 20-30 handcrafted tasks for the Intro Python curriculum.
    
    These are handcrafted (not AI-generated) to ensure:
    - Interpretability
    - Debugging clarity
    - Replay validity
    - Educational soundness
    """
    # Ensure concepts are initialized
    registry = get_registry()
    if not registry._concepts:
        initialize_intro_python_curriculum()
    
    # === SEQUENCE TASKS (3 tasks) ===
    
    # Task 1: Basic sequence MCQ
    task_seq_1 = LearningTask(
        id="sequence_1_mcq",
        concept_id="sequence",
        task_type=TaskType.MCQ,
        difficulty=0.2,
        prompt="What will be printed after executing these lines in order?\n\nprint('Hello')\nprint('World')",
        expected_answer="Hello\nWorld",
        misconception_target="order_matters",
        evaluation_mode="binary",
        hints=[
            "Computers execute instructions from top to bottom",
            "Each print statement outputs on a new line"
        ],
        explanation="Python executes statements in sequence. First 'Hello' is printed, then 'World'.",
        estimated_time_seconds=30,
        translations={
            "en": {
                "prompt": "What will be printed after executing these lines in order?\n\nprint('Hello')\nprint('World')",
                "explanation": "Python executes statements in sequence. First 'Hello' is printed, then 'World'."
            },
            "id": {
                "prompt": "Apa yang akan dicetak setelah mengeksekusi baris-baris ini secara berurutan?\n\nprint('Hello')\nprint('World')",
                "explanation": "Python mengeksekusi pernyataan secara berurutan. Pertama 'Hello' dicetak, lalu 'World'."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "order_matters",
            "version": "1.0"
        }
    )
    registry.register_task(task_seq_1)
    
    # Task 2: Sequence Parsons problem
    task_seq_2 = LearningTask(
        id="sequence_2_parsons",
        concept_id="sequence",
        task_type=TaskType.PARSONS,
        difficulty=0.3,
        prompt="Arrange these lines to print a greeting and farewell in the correct order:\n\nLines: ['print(\"Goodbye\")', 'print(\"Hello\")']",
        expected_answer="print(\"Hello\")\nprint(\"Goodbye\")",
        misconception_target="sequential_execution",
        evaluation_mode="binary",
        hints=[
            "Greetings typically come before farewells",
            "Execute from top to bottom"
        ],
        explanation="The correct sequence prints 'Hello' first, then 'Goodbye'.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "Arrange these lines to print a greeting and farewell in the correct order:\n\nLines: ['print(\"Goodbye\")', 'print(\"Hello\")']",
                "explanation": "The correct sequence prints 'Hello' first, then 'Goodbye'."
            },
            "id": {
                "prompt": "Susun baris-baris ini untuk mencetak sapaan dan perpisahan dalam urutan yang benar:\n\nBaris: ['print(\"Goodbye\")', 'print(\"Hello\")']",
                "explanation": "Urutan yang benar mencetak 'Hello' terlebih dahulu, lalu 'Goodbye'."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "sequential_execution",
            "version": "1.0"
        }
    )
    registry.register_task(task_seq_2)
    
    # Task 3: Sequence code trace
    task_seq_3 = LearningTask(
        id="sequence_3_trace",
        concept_id="sequence",
        task_type=TaskType.CODE_TRACE,
        difficulty=0.4,
        prompt="Trace the output of this code:\n\nx = 5\nprint(x)\nx = 10\nprint(x)",
        expected_answer="5\n10",
        misconception_target="sequential_execution",
        evaluation_mode="binary",
        hints=[
            "Variables can be reassigned",
            "Each print shows the current value"
        ],
        explanation="First x is 5, so 5 is printed. Then x becomes 10, so 10 is printed.",
        estimated_time_seconds=60,
        translations={
            "en": {
                "prompt": "Trace the output of this code:\n\nx = 5\nprint(x)\nx = 10\nprint(x)",
                "explanation": "First x is 5, so 5 is printed. Then x becomes 10, so 10 is printed."
            },
            "id": {
                "prompt": "Lacak output dari kode ini:\n\nx = 5\nprint(x)\nx = 10\nprint(x)",
                "explanation": "Pertama x adalah 5, jadi 5 dicetak. Lalu x menjadi 10, jadi 10 dicetak."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "sequential_execution",
            "version": "1.0"
        }
    )
    registry.register_task(task_seq_3)
    
    # === VARIABLES TASKS (3 tasks) ===
    
    # Task 4: Variable assignment MCQ
    task_var_1 = LearningTask(
        id="variables_1_mcq",
        concept_id="variables",
        task_type=TaskType.MCQ,
        difficulty=0.3,
        prompt="What is the value of x after this code?\n\nx = 7",
        expected_answer="7",
        misconception_target="variable_assignment",
        evaluation_mode="binary",
        hints=[
            "The = operator assigns the right side to the left side",
            "x now holds the value 7"
        ],
        explanation="The assignment x = 7 stores the value 7 in the variable x.",
        estimated_time_seconds=30,
        translations={
            "en": {
                "prompt": "What is the value of x after this code?\n\nx = 7",
                "explanation": "The assignment x = 7 stores the value 7 in the variable x."
            },
            "id": {
                "prompt": "Berapa nilai x setelah kode ini?\n\nx = 7",
                "explanation": "Penugasan x = 7 menyimpan nilai 7 dalam variabel x."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "variable_assignment",
            "version": "1.0"
        }
    )
    registry.register_task(task_var_1)
    
    # Task 5: Variable update MCQ
    task_var_2 = LearningTask(
        id="variables_2_mcq",
        concept_id="variables",
        task_type=TaskType.MCQ,
        difficulty=0.4,
        prompt="What is the value of x after this code?\n\nx = 3\nx = x + 2",
        expected_answer="5",
        misconception_target="variable_update",
        evaluation_mode="binary",
        hints=[
            "First x becomes 3",
            "Then x + 2 is calculated (3 + 2 = 5) and stored back in x"
        ],
        explanation="x starts as 3, then x + 2 evaluates to 5, which is stored back in x.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "What is the value of x after this code?\n\nx = 3\nx = x + 2",
                "explanation": "x starts as 3, then x + 2 evaluates to 5, which is stored back in x."
            },
            "id": {
                "prompt": "Berapa nilai x setelah kode ini?\n\nx = 3\nx = x + 2",
                "explanation": "x dimulai sebagai 3, lalu x + 2 dievaluasi menjadi 5, yang disimpan kembali ke x."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "variable_update",
            "version": "1.0"
        }
    )
    registry.register_task(task_var_2)
    
    # Task 6: Variable short answer
    task_var_3 = LearningTask(
        id="variables_3_short",
        concept_id="variables",
        task_type=TaskType.SHORT_ANSWER,
        difficulty=0.5,
        prompt="Write code to store your name in a variable called 'my_name'.",
        expected_answer="my_name = \"your name\"",
        misconception_target="variable_assignment",
        evaluation_mode="partial",
        hints=[
            "Use the = operator",
            "String values need quotes"
        ],
        explanation="Variables store values. my_name = \"John\" stores the string 'John' in my_name.",
        estimated_time_seconds=60,
        translations={
            "en": {
                "prompt": "Write code to store your name in a variable called 'my_name'.",
                "explanation": "Variables store values. my_name = \"John\" stores the string 'John' in my_name."
            },
            "id": {
                "prompt": "Tulis kode untuk menyimpan nama Anda dalam variabel bernama 'my_name'.",
                "explanation": "Variabel menyimpan nilai. my_name = \"John\" menyimpan string 'John' di my_name."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "variable_assignment",
            "version": "1.0"
        }
    )
    registry.register_task(task_var_3)
    
    # === CONDITIONALS TASKS (3 tasks) ===
    
    # Task 7: Simple if statement MCQ
    task_cond_1 = LearningTask(
        id="conditionals_1_mcq",
        concept_id="conditionals",
        task_type=TaskType.MCQ,
        difficulty=0.4,
        prompt="What will be printed?\n\nx = 10\nif x > 5:\n    print('Big')\nprint('Done')",
        expected_answer="Big\nDone",
        misconception_target="boolean_logic",
        evaluation_mode="binary",
        hints=[
            "10 > 5 is True, so the if block executes",
            "print('Done') is outside the if block, so it always runs"
        ],
        explanation="Since 10 > 5 is True, 'Big' is printed. Then 'Done' is printed regardless.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "What will be printed?\n\nx = 10\nif x > 5:\n    print('Big')\nprint('Done')",
                "explanation": "Since 10 > 5 is True, 'Big' is printed. Then 'Done' is printed regardless."
            },
            "id": {
                "prompt": "Apa yang akan dicetak?\n\nx = 10\nif x > 5:\n    print('Big')\nprint('Done')",
                "explanation": "Karena 10 > 5 adalah True, 'Big' dicetak. Lalu 'Done' dicetak terlepas dari kondisi."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "boolean_logic",
            "version": "1.0"
        }
    )
    registry.register_task(task_cond_1)
    
    # Task 8: If-else MCQ
    task_cond_2 = LearningTask(
        id="conditionals_2_mcq",
        concept_id="conditionals",
        task_type=TaskType.MCQ,
        difficulty=0.5,
        prompt="What will be printed?\n\nx = 3\nif x > 5:\n    print('Big')\nelse:\n    print('Small')",
        expected_answer="Small",
        misconception_target="branching",
        evaluation_mode="binary",
        hints=[
            "3 > 5 is False",
            "When the if condition is False, the else block executes"
        ],
        explanation="Since 3 > 5 is False, the if block is skipped and the else block prints 'Small'.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "What will be printed?\n\nx = 3\nif x > 5:\n    print('Big')\nelse:\n    print('Small')",
                "explanation": "Since 3 > 5 is False, the if block is skipped and the else block prints 'Small'."
            },
            "id": {
                "prompt": "Apa yang akan dicetak?\n\nx = 3\nif x > 5:\n    print('Big')\nelse:\n    print('Small')",
                "explanation": "Karena 3 > 5 adalah False, blok if dilewati dan blok else mencetak 'Small'."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "branching",
            "version": "1.0"
        }
    )
    registry.register_task(task_cond_2)
    
    # Task 9: Conditional Parsons
    task_cond_3 = LearningTask(
        id="conditionals_3_parsons",
        concept_id="conditionals",
        task_type=TaskType.PARSONS,
        difficulty=0.6,
        prompt="Arrange these lines to check if a number is positive:\n\nLines: ['if x > 0:', 'print(\"Positive\")', 'x = 5']",
        expected_answer="x = 5\nif x > 0:\n    print(\"Positive\")",
        misconception_target="branching",
        evaluation_mode="binary",
        hints=[
            "First assign the value to check",
            "Then use if to test the condition",
            "Indentation matters in Python"
        ],
        explanation="Assign x first, then check if it's positive with an if statement.",
        estimated_time_seconds=60,
        translations={
            "en": {
                "prompt": "Arrange these lines to check if a number is positive:\n\nLines: ['if x > 0:', 'print(\"Positive\")', 'x = 5']",
                "explanation": "Assign x first, then check if it's positive with an if statement."
            },
            "id": {
                "prompt": "Susun baris-baris ini untuk memeriksa apakah sebuah bilangan positif:\n\nBaris: ['if x > 0:', 'print(\"Positive\")', 'x = 5']",
                "explanation": "Tetapkan x terlebih dahulu, lalu periksa apakah positif dengan pernyataan if."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "branching",
            "version": "1.0"
        }
    )
    registry.register_task(task_cond_3)
    
    # === LOOPS TASKS (3 tasks) ===
    
    # Task 10: For loop MCQ
    task_loop_1 = LearningTask(
        id="loops_1_mcq",
        concept_id="loops",
        task_type=TaskType.MCQ,
        difficulty=0.5,
        prompt="How many times will 'Hello' be printed?\n\nfor i in range(3):\n    print('Hello')",
        expected_answer="3",
        misconception_target="iteration",
        evaluation_mode="binary",
        hints=[
            "range(3) generates 0, 1, 2",
            "The loop runs once for each value in the range"
        ],
        explanation="range(3) produces 3 values (0, 1, 2), so the loop body executes 3 times.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "How many times will 'Hello' be printed?\n\nfor i in range(3):\n    print('Hello')",
                "explanation": "range(3) produces 3 values (0, 1, 2), so the loop body executes 3 times."
            },
            "id": {
                "prompt": "Berapa kali 'Hello' akan dicetak?\n\nfor i in range(3):\n    print('Hello')",
                "explanation": "range(3) menghasilkan 3 nilai (0, 1, 2), jadi tubuh loop dieksekusi 3 kali."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "iteration",
            "version": "1.0"
        }
    )
    registry.register_task(task_loop_1)
    
    # Task 11: Loop with accumulation MCQ
    task_loop_2 = LearningTask(
        id="loops_2_mcq",
        concept_id="loops",
        task_type=TaskType.MCQ,
        difficulty=0.6,
        prompt="What is the value of total after this code?\n\ntotal = 0\nfor i in range(3):\n    total = total + i",
        expected_answer="3",
        misconception_target="accumulation",
        evaluation_mode="binary",
        hints=[
            "Trace each iteration: i=0, i=1, i=2",
            "total accumulates: 0+0=0, 0+1=1, 1+2=3"
        ],
        explanation="Iteration 0: total=0+0=0. Iteration 1: total=0+1=1. Iteration 2: total=1+2=3.",
        estimated_time_seconds=60,
        translations={
            "en": {
                "prompt": "What is the value of total after this code?\n\ntotal = 0\nfor i in range(3):\n    total = total + i",
                "explanation": "Iteration 0: total=0+0=0. Iteration 1: total=0+1=1. Iteration 2: total=1+2=3."
            },
            "id": {
                "prompt": "Berapa nilai total setelah kode ini?\n\ntotal = 0\nfor i in range(3):\n    total = total + i",
                "explanation": "Iterasi 0: total=0+0=0. Iterasi 1: total=0+1=1. Iterasi 2: total=1+2=3."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "accumulation",
            "version": "1.0"
        }
    )
    registry.register_task(task_loop_2)
    
    # Task 12: Loop Parsons
    task_loop_3 = LearningTask(
        id="loops_3_parsons",
        concept_id="loops",
        task_type=TaskType.PARSONS,
        difficulty=0.7,
        prompt="Arrange these lines to print numbers 0 to 2:\n\nLines: ['for i in range(3):', 'print(i)']",
        expected_answer="for i in range(3):\n    print(i)",
        misconception_target="iteration",
        evaluation_mode="binary",
        hints=[
            "Start with the for loop",
            "Indent the body of the loop"
        ],
        explanation="The for loop iterates over range(3), printing each value.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "Arrange these lines to print numbers 0 to 2:\n\nLines: ['for i in range(3):', 'print(i)']",
                "explanation": "The for loop iterates over range(3), printing each value."
            },
            "id": {
                "prompt": "Susun baris-baris ini untuk mencetak angka 0 hingga 2:\n\nBaris: ['for i in range(3):', 'print(i)']",
                "explanation": "Loop for melakukan iterasi atas range(3), mencetak setiap nilai."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "iteration",
            "version": "1.0"
        }
    )
    registry.register_task(task_loop_3)
    
    # === DECOMPOSITION TASKS (2 tasks) ===
    
    # Task 13: Decomposition MCQ
    task_decomp_1 = LearningTask(
        id="decomposition_1_mcq",
        concept_id="decomposition",
        task_type=TaskType.MCQ,
        difficulty=0.6,
        prompt="To solve 'calculate the average of a list of numbers', what is the first step in decomposition?",
        expected_answer="Find the sum of the numbers",
        misconception_target="subproblem_breakdown",
        evaluation_mode="partial",
        hints=[
            "Average = sum / count",
            "You need both the sum and the count"
        ],
        explanation="Decomposition breaks problems: first find the sum, then count items, then divide.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "To solve 'calculate the average of a list of numbers', what is the first step in decomposition?",
                "explanation": "Decomposition breaks problems: first find the sum, then count items, then divide."
            },
            "id": {
                "prompt": "Untuk menyelesaikan 'hitung rata-rata daftar angka', apa langkah pertama dalam dekomposisi?",
                "explanation": "Dekomposisi memecah masalah: pertama temukan jumlah, lalu hitung item, lalu bagi."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "subproblem_breakdown",
            "version": "1.0"
        }
    )
    registry.register_task(task_decomp_1)
    
    # Task 14: Decomposition short answer
    task_decomp_2 = LearningTask(
        id="decomposition_2_short",
        concept_id="decomposition",
        task_type=TaskType.SHORT_ANSWER,
        difficulty=0.7,
        prompt="Break down 'make a sandwich' into 3 steps:",
        expected_answer="Get bread, add filling, put bread together",
        misconception_target="subproblem_breakdown",
        evaluation_mode="partial",
        hints=[
            "Think about the physical actions",
            "Order matters for the steps"
        ],
        explanation="Decomposition identifies subproblems: prepare ingredients, assemble, serve.",
        estimated_time_seconds=60,
        translations={
            "en": {
                "prompt": "Break down 'make a sandwich' into 3 steps:",
                "explanation": "Decomposition identifies subproblems: prepare ingredients, assemble, serve."
            },
            "id": {
                "prompt": "Pecah 'buat sandwich' menjadi 3 langkah:",
                "explanation": "Dekomposisi mengidentifikasi submasalah: siapkan bahan, rakit, sajikan."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "subproblem_breakdown",
            "version": "1.0"
        }
    )
    registry.register_task(task_decomp_2)
    
    # === FUNCTIONS TASKS (3 tasks) ===
    
    # Task 15: Function definition MCQ
    task_func_1 = LearningTask(
        id="functions_1_mcq",
        concept_id="functions",
        task_type=TaskType.MCQ,
        difficulty=0.6,
        prompt="What keyword is used to define a function in Python?",
        expected_answer="def",
        misconception_target="function_definition",
        evaluation_mode="binary",
        hints=[
            "It's a short keyword",
            "It stands for 'define'"
        ],
        explanation="Python uses 'def' to define functions, e.g., def my_function():",
        estimated_time_seconds=30,
        translations={
            "en": {
                "prompt": "What keyword is used to define a function in Python?",
                "explanation": "Python uses 'def' to define functions, e.g., def my_function():"
            },
            "id": {
                "prompt": "Kata kunci apa yang digunakan untuk mendefinisikan fungsi di Python?",
                "explanation": "Python menggunakan 'def' untuk mendefinisikan fungsi, misalnya def my_function():"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "function_definition",
            "version": "1.0"
        }
    )
    registry.register_task(task_func_1)
    
    # Task 16: Function with parameter MCQ
    task_func_2 = LearningTask(
        id="functions_2_mcq",
        concept_id="functions",
        task_type=TaskType.MCQ,
        difficulty=0.7,
        prompt="What will be printed?\n\ndef greet(name):\n    print('Hello ' + name)\ngreet('Alice')",
        expected_answer="Hello Alice",
        misconception_target="parameters",
        evaluation_mode="binary",
        hints=[
            "The function takes 'name' as a parameter",
            "'Alice' is passed as the argument"
        ],
        explanation="The function greet is called with 'Alice', so it prints 'Hello Alice'.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "What will be printed?\n\ndef greet(name):\n    print('Hello ' + name)\ngreet('Alice')",
                "explanation": "The function greet is called with 'Alice', so it prints 'Hello Alice'."
            },
            "id": {
                "prompt": "Apa yang akan dicetak?\n\ndef greet(name):\n    print('Hello ' + name)\ngreet('Alice')",
                "explanation": "Fungsi greet dipanggil dengan 'Alice', jadi mencetak 'Hello Alice'."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "parameters",
            "version": "1.0"
        }
    )
    registry.register_task(task_func_2)
    
    # Task 17: Function Parsons
    task_func_3 = LearningTask(
        id="functions_3_parsons",
        concept_id="functions",
        task_type=TaskType.PARSONS,
        difficulty=0.8,
        prompt="Arrange these lines to define a function that doubles a number:\n\nLines: ['return x * 2', 'def double(x):']",
        expected_answer="def double(x):\n    return x * 2",
        misconception_target="return_values",
        evaluation_mode="binary",
        hints=[
            "Start with the function definition",
            "Indent the return statement"
        ],
        explanation="The function double takes x and returns x multiplied by 2.",
        estimated_time_seconds=60,
        translations={
            "en": {
                "prompt": "Arrange these lines to define a function that doubles a number:\n\nLines: ['return x * 2', 'def double(x):']",
                "explanation": "The function double takes x and returns x multiplied by 2."
            },
            "id": {
                "prompt": "Susun baris-baris ini untuk mendefinisikan fungsi yang menggandakan angka:\n\nBaris: ['return x * 2', 'def double(x):']",
                "explanation": "Fungsi double mengambil x dan mengembalikan x dikali 2."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "return_values",
            "version": "1.0"
        }
    )
    registry.register_task(task_func_3)
    
    # === LISTS TASKS (3 tasks) ===
    
    # Task 18: List indexing MCQ
    task_list_1 = LearningTask(
        id="lists_1_mcq",
        concept_id="lists",
        task_type=TaskType.MCQ,
        difficulty=0.6,
        prompt="What is fruits[0] if fruits = ['apple', 'banana', 'cherry']?",
        expected_answer="apple",
        misconception_target="indexing",
        evaluation_mode="binary",
        hints=[
            "Python lists are 0-indexed",
            "The first element is at index 0"
        ],
        explanation="List indexing starts at 0, so fruits[0] returns 'apple'.",
        estimated_time_seconds=30,
        translations={
            "en": {
                "prompt": "What is fruits[0] if fruits = ['apple', 'banana', 'cherry']?",
                "explanation": "List indexing starts at 0, so fruits[0] returns 'apple'."
            },
            "id": {
                "prompt": "Apa fruits[0] jika fruits = ['apple', 'banana', 'cherry']?",
                "explanation": "Indeks daftar dimulai dari 0, jadi fruits[0] mengembalikan 'apple'."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "indexing",
            "version": "1.0"
        }
    )
    registry.register_task(task_list_1)
    
    # Task 19: List append MCQ
    task_list_2 = LearningTask(
        id="lists_2_mcq",
        concept_id="lists",
        task_type=TaskType.MCQ,
        difficulty=0.7,
        prompt="What is fruits after this code?\n\nfruits = ['apple']\nfruits.append('banana')",
        expected_answer="['apple', 'banana']",
        misconception_target="list_operations",
        evaluation_mode="binary",
        hints=[
            "append adds to the end of the list",
            "The original list is modified"
        ],
        explanation="append adds 'banana' to the end, resulting in ['apple', 'banana'].",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "What is fruits after this code?\n\nfruits = ['apple']\nfruits.append('banana')",
                "explanation": "append adds 'banana' to the end, resulting in ['apple', 'banana']."
            },
            "id": {
                "prompt": "Apa fruits setelah kode ini?\n\nfruits = ['apple']\nfruits.append('banana')",
                "explanation": "append menambahkan 'banana' ke akhir, menghasilkan ['apple', 'banana']."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "list_operations",
            "version": "1.0"
        }
    )
    registry.register_task(task_list_2)
    
    # Task 20: List iteration MCQ
    task_list_3 = LearningTask(
        id="lists_3_mcq",
        concept_id="lists",
        task_type=TaskType.MCQ,
        difficulty=0.8,
        prompt="How many times will the loop run?\n\nfor item in ['a', 'b', 'c']:\n    print(item)",
        expected_answer="3",
        misconception_target="iteration",
        evaluation_mode="binary",
        hints=[
            "The loop iterates over each item in the list",
            "There are 3 items in the list"
        ],
        explanation="The list has 3 items, so the loop body executes 3 times.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "How many times will the loop run?\n\nfor item in ['a', 'b', 'c']:\n    print(item)",
                "explanation": "The list has 3 items, so the loop body executes 3 times."
            },
            "id": {
                "prompt": "Berapa kali loop akan berjalan?\n\nfor item in ['a', 'b', 'c']:\n    print(item)",
                "explanation": "Daftar memiliki 3 item, jadi tubuh loop dieksekusi 3 kali."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "iteration",
            "version": "1.0"
        }
    )
    registry.register_task(task_list_3)
    
    # === DICTIONARIES TASKS (2 tasks) ===
    
    # Task 21: Dictionary lookup MCQ
    task_dict_1 = LearningTask(
        id="dictionaries_1_mcq",
        concept_id="dictionaries",
        task_type=TaskType.MCQ,
        difficulty=0.7,
        prompt="What is scores['Alice'] if scores = {'Alice': 95, 'Bob': 87}?",
        expected_answer="95",
        misconception_target="key_value_pairs",
        evaluation_mode="binary",
        hints=[
            "Dictionaries use keys to access values",
            "The key 'Alice' maps to the value 95"
        ],
        explanation="Dictionary lookup uses the key: scores['Alice'] returns 95.",
        estimated_time_seconds=30,
        translations={
            "en": {
                "prompt": "What is scores['Alice'] if scores = {'Alice': 95, 'Bob': 87}?",
                "explanation": "Dictionary lookup uses the key: scores['Alice'] returns 95."
            },
            "id": {
                "prompt": "Apa scores['Alice'] jika scores = {'Alice': 95, 'Bob': 87}?",
                "explanation": "Pencarian kamus menggunakan kunci: scores['Alice'] mengembalikan 95."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "key_value_pairs",
            "version": "1.0"
        }
    )
    registry.register_task(task_dict_1)
    
    # Task 22: Dictionary add MCQ
    task_dict_2 = LearningTask(
        id="dictionaries_2_mcq",
        concept_id="dictionaries",
        task_type=TaskType.MCQ,
        difficulty=0.8,
        prompt="What is scores after this code?\n\nscores = {'Alice': 95}\nscores['Bob'] = 87",
        expected_answer="{'Alice': 95, 'Bob': 87}",
        misconception_target="key_value_pairs",
        evaluation_mode="binary",
        hints=[
            "You can add new key-value pairs with assignment",
            "The original dictionary is modified"
        ],
        explanation="Assignment adds a new key-value pair, resulting in {'Alice': 95, 'Bob': 87}.",
        estimated_time_seconds=45,
        translations={
            "en": {
                "prompt": "What is scores after this code?\n\nscores = {'Alice': 95}\nscores['Bob'] = 87",
                "explanation": "Assignment adds a new key-value pair, resulting in {'Alice': 95, 'Bob': 87}."
            },
            "id": {
                "prompt": "Apa scores setelah kode ini?\n\nscores = {'Alice': 95}\nscores['Bob'] = 87",
                "explanation": "Penugasan menambahkan pasangan kunci-nilai baru, menghasilkan {'Alice': 95, 'Bob': 87}."
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "misconception_targeted": "key_value_pairs",
            "version": "1.0"
        }
    )
    registry.register_task(task_dict_2)
    
    print(f"✅ Task registry initialized with {len(registry._tasks)} handcrafted tasks")
    
    return registry


if __name__ == "__main__":
    # Initialize and test the task registry
    registry = initialize_handcrafted_tasks()
    
    print("\n📊 Task Registry Statistics:")
    print(f"  Total concepts: {len(registry._concepts)}")
    print(f"  Total tasks: {len(registry._tasks)}")
    
    print("\n📝 Tasks by Concept:")
    for concept_id in registry._concepts:
        tasks = registry.get_tasks_for_concept(concept_id)
        print(f"  {concept_id}: {len(tasks)} tasks")
        for task in tasks:
            print(f"    - {task.id} ({task.task_type.value}, difficulty: {task.difficulty})")
