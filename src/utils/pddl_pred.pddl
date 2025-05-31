
(define (problem blocksworld_fsp_example_problem)
    (:domain blocksworld)
    (:requirements :strips)
    (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)
    (:init 
        ; Arm state
        (arm-empty)
        ; 1 block stack
        (clear b1) (on-table b1)
        ; 2 blocks stack
        (clear b2) (on b2 b3) (on-table b3)
        ; 3 blocks stack
        (clear b4) (on b4 b5) (on b5 b6) (on-table b6)
        ; 4 blocks stack
        (clear b7) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b10)
    )
    (:goal (and
        ; Direct translation of the goal's natural language description to predicates
        (arm-empty)
        (clear b1) (on-table b1)
        (clear b2) (on-table b2)
        (clear b3) (on-table b3)
        (clear b4) (on-table b4)
        (clear b5) (on b5 b6) (on b6 b7) (on-table b7)
        (clear b8) (on b8 b9) (on b9 b10) (on-table b10)
    ))
)