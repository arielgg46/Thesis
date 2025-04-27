def expand_requirements(enabled, expansions):
    """
    Recursively expand a set of requirements based on the expansion rules.
    """
    expanded = set(enabled)
    changed = True

    while changed:
        changed = False
        for req, implied in expansions.items():
            if req in expanded and not all(r in expanded for r in implied):
                expanded.update(implied)
                changed = True

    return expanded

def filter_rules_by_requirements(rules_with_reqs, enabled_requirements):
    """
    Filters rules by checking whether their (expanded) requirements are enabled.

    Args:
        rules_with_reqs (list[tuple[str, list[str]]]): 
            List of (rule, requirements) pairs.
        enabled_requirements (list[str]): 
            List of enabled requirements.

    Returns:
        str: Concatenated string of rules that pass the requirement filter.
    """
    REQUIREMENT_EXPANSIONS = {
        ":adl": [
            ":strips", ":typing", ":negative-preconditions", ":disjunctive-preconditions",
            ":equality", ":existential-preconditions", ":universal-preconditions", ":conditional-effects"
        ],
        ":quantified-preconditions": [":existential-preconditions", ":universal-preconditions"],
        ":fluents": [":numeric-fluents", ":object-fluents"],
    }

    expanded_enabled = expand_requirements(enabled_requirements, REQUIREMENT_EXPANSIONS)

    valid_rules = [
        rule for rule, reqs in rules_with_reqs
        if all(r in expanded_enabled for r in reqs)
    ]

    return "\n".join(valid_rules)


PDDL_PROBLEM_BNF = [
    ("<problem> ::= (define (problem <name>) (:domain <name>) [<require-def>] [<object declaration>] <init> <goal>", []),
    ("[<constraints>]", ["constraints"]),
    ("[<metric-spec>]", ["numeric-fluents"]),
    ("[<length-spec>])", []),
    ("<object declaration> ::= (:objects <typed list (name)>)", []),
    ("<init> ::= (:init <init-el>*)", []),
    ("<init-el> ::= <literal(name)>", []),
    ("<init-el> ::= (at <number> <literal(name)>)", ["timed−initial−literals"]),
    ("<init-el> ::= (= <basic-function-term> <number>)", ["numeric-fluents"]),
    ("<init-el> ::= (= <basic-function-term> <name>)", ["object-fluents"]),
    ("<basic-function-term> ::= <function-symbol>", []),
    ("<basic-function-term> ::= (<function-symbol> <name>*)", []),
    ("<goal> ::= (:goal <pre-GD>)", []),
    ("<constraints> ::= (:constraints <pref-con-GD>)", ["constraints"]),
    ("<pref-con-GD> ::= (and <pref-con-GD>*)", []),
    ("<pref-con-GD> ::= (forall (<typed list (variable)>) <pref-con-GD>)", ["universal−preconditions"]),
    ("<pref-con-GD> ::= (preference [<pref-name>] <con-GD>)", ["preferences"]),
    ("<pref-con-GD> ::= <con-GD>", []),
    ("<con-GD> ::= (and <con-GD>*)", []),
    ("<con-GD> ::= (forall (<typed list (variable)>) <con-GD>)", []),
    ("<con-GD> ::= (at end <GD>)", []),
    ("<con-GD> ::= (always <GD>)", []),
    ("<con-GD> ::= (sometime <GD>)", []),
    ("<con-GD> ::= (within <number> <GD>)", []),
    ("<con-GD> ::= (at-most-once <GD>)", []),
    ("<con-GD> ::= (sometime-after <GD> <GD>)", []),
    ("<con-GD> ::= (sometime-before <GD> <GD>)", []),
    ("<con-GD> ::= (always-within <number> <GD> <GD>)", []),
    ("<con-GD> ::= (hold-during <number> <number> <GD>)", []),
    ("<con-GD> ::= (hold-after <number> <GD>)", []),
    ("<metric-spec> ::= (:metric <optimization> <metric-f-exp>)", ["numeric-fluents"]),
    ("<optimization> ::= minimize", []),
    ("<optimization> ::= maximize", []),
    ("<metric-f-exp> ::= (<binary-op> <metric-f-exp> <metric-f-exp>)", []),
    ("<metric-f-exp> ::= (<multi-op> <metric-f-exp> <metric-f-exp>+)", []),
    ("<metric-f-exp> ::= (- <metric-f-exp>)", []),
    ("<metric-f-exp> ::= <number>", []),
    ("<metric-f-exp> ::= (<function-symbol> <name>*)", []),
    ("<metric-f-exp> ::= <function-symbol>", []),
    ("<metric-f-exp> ::= total-time", []),
    ("<metric-f-exp> ::= (is-violated <pref-name>)", ["preferences"]),
    ("<length-spec> ::= (:length [(:serial <integer>)] [(:parallel <integer>)])", [])
]

PDDL_DOMAIN_BNF = [
    ("<domain> ::= (define (domain <name>) [<require-def>]", []),
    ("[<types-def>]", ["typing"]),
    ("[<constants-def>] [<predicates-def>]", []),
    ("[<functions-def>]", []),
    ("[<constraints>] <structure-def>*)", []),
    ("<require-def> ::= (:requirements <require-key>+)", []),
    ("<require-key> ::= :strips | :typing | :negative-preconditions | :disjunctive-preconditions | :equality | :existential-preconditions | :universal-preconditions | :quantified-preconditions | :conditional-effects | :numeric-fluents | :object-fluents | :fluents | :adl | :durative-actions | :duration-inequalities | :continuous-effects | :derived-predicates | :timed-initial-literals | :preferences | :constraints | :action-costs", []), # not sure about this
    ("<types-def> ::= (:types <typed list (name)>)", ["typing"]),
    ("<constants-def> ::= (:constants <typed list (name)>)", []),
    ("<predicates-def> ::= (:predicates <atomic formula skeleton>+)", []),
    ("<atomic formula skeleton> ::= (<predicate> <typed list (variable)>)", []),
    ("<predicate> ::= <name>", []),
    ("<variable> ::= ?<name>", []),
    ("<atomic function skeleton> ::= (<function-symbol> <typed list (variable)>)", []),
    ("<function-symbol> ::= <name>", []),
    ("<functions-def> ::= (:functions <function typed list (atomic function skeleton)>)", ["fluents"]),
    ("<function typed list (x)> ::= x+ - <function type> <function typed list(x)>", []),
    ("<function typed list (x)> ::= x+", ["numeric-fluents"]),
    ("<function type> ::= number", ["numeric-fluents"]),
    ("<function type> ::= <type>", ["typing", "object-fluents"]),
    ("<constraints> ::= (:constraints <con-GD>)", ["constraints"]),
    ("<structure-def> ::= <action-def>", []),
    ("<structure-def> ::= <durative-action-def>", ["durative−actions"]),
    ("<structure-def> ::= <derived-def>", ["derived−predicates"]),
    ("<typed list (x)> ::= x*", []),
    ("<typed list (x)> ::= x+ - <type> <typed list(x)>", ["typing"]),
    ("<primitive-type> ::= <name>", []),
    ("<primitive-type> ::= object", []),
    ("<type> ::= (either <primitive-type>+)", []),
    ("<type> ::= <primitive-type>", []),
    ("<emptyOr (x)> ::= ()", []),
    ("<emptyOr (x)> ::= x", []),
    ("<action-def> ::= (:action <action-symbol> :parameters (<typed list (variable)>) <action-def body>)", []),
    ("<action-symbol> ::= <name>", []),
    ("<action-def body> ::= [:precondition <emptyOr (pre-GD)>] [:effect <emptyOr (effect)>]", []),
    ("<pre-GD> ::= <pref-GD>", []),
    ("<pre-GD> ::= (and <pre-GD>*)", []),
    ("<pre-GD> ::= (forall (<typed list(variable)>) <pre-GD>)", ["universal−preconditions"]),
    ("<pref-GD> ::= (preference [<pref-name>] <GD>)", ["preferences"]),
    ("<pref-GD> ::= <GD>", []),
    ("<pref-name> ::= <name>", []),
    ("<GD> ::= <atomic formula(term)>", []),
    ("<GD> ::= <literal(term)>", ["negative−preconditions"]),
    ("<GD> ::= (and <GD>*)", []),
    ("<GD> ::= (or <GD>*)", ["disjunctive−preconditions"]),
    ("<GD> ::= (not <GD>)", ["disjunctive−preconditions"]),
    ("<GD> ::= (imply <GD> <GD>)", ["disjunctive−preconditions"]),
    ("<GD> ::= (exists (<typed list(variable)>) <GD> )", ["existential−preconditions"]),
    ("<GD> ::= (forall (<typed list(variable)>) <GD> )", ["universal−preconditions"]),
    ("<GD> ::= <f-comp>", ["numeric-fluents"]),
    ("<f-comp> ::= (<binary-comp> <f-exp> <f-exp>)", []),
    ("<literal(t)> ::= <atomic formula(t)>", []),
    ("<literal(t)> ::= (not <atomic formula(t)>)", []),
    ("<atomic formula(t)> ::= (<predicate> t*)", []),
    ("<atomic formula(t)> ::= (= t t)", ["equality"]),
    ("<term> ::= <name>", []),
    ("<term> ::= <variable>", []),
    ("<term> ::= <function-term>", ["object-fluents"]),
    ("<function-term> ::= (<function-symbol> <term>*)", ["object-fluents"]),
    ("<f-exp> ::= <number>", ["numeric-fluents"]),
    ("<f-exp> ::= (<binary-op> <f-exp> <f-exp>)", ["numeric-fluents"]),
    ("<f-exp> ::= (<multi-op> <f-exp> <f-exp>+)", ["numeric-fluents"]),
    ("<f-exp> ::= (- <f-exp>)", ["numeric-fluents"]),
    ("<f-exp> ::= <f-head>", ["numeric-fluents"]),
    ("<f-head> ::= (<function-symbol> <term>*)", []),
    ("<f-head> ::= <function-symbol>", []),
    ("<binary-op> ::= <multi-op>", []),
    ("<binary-op> ::= −", []),
    ("<binary-op> ::= /", []),
    ("<multi-op> ::= *", []),
    ("<multi-op> ::= +", []),
    ("<binary-comp> ::= >", []),
    ("<binary-comp> ::= <", []),
    ("<binary-comp> ::= =", []),
    ("<binary-comp> ::= >=", []),
    ("<binary-comp> ::= <=", []),
    ("<name> ::= <letter> <any char>*", []),
    ("<letter> ::= a..z | A..Z", []),
    ("<any char> ::= <letter> | <digit> | - | _", []),
    ("<number> ::= <digit>+ [<decimal>]", []),
    ("<digit> ::= 0..9", []),
    ("<decimal> ::= .<digit>+", []),
    ("<effect> ::= (and <c-effect>*)", []),
    ("<effect> ::= <c-effect>", []),
    ("<c-effect> ::= (forall (<typed list (variable)>) <effect>)", ["conditional−effects"]),
    ("<c-effect> ::= (when <GD> <cond-effect>)", ["conditional−effects"]),
    ("<c-effect> ::= <p-effect>", []),
    ("<p-effect> ::= (not <atomic formula(term)>)", []),
    ("<p-effect> ::= <atomic formula(term)>", []),
    ("<p-effect> ::= (<assign-op> <f-head> <f-exp>)", ["numeric-fluents"]),
    ("<p-effect> ::= (assign <function-term> <term>)", ["object-fluents"]),
    ("<p-effect> ::= (assign <function-term> undefined)", ["object-fluents"]),
    ("<cond-effect> ::= (and <p-effect>*)", []),
    ("<cond-effect> ::= <p-effect>", []),
    ("<assign-op> ::= assign", []),
    ("<assign-op> ::= scale-up", []),
    ("<assign-op> ::= scale-down", []),
    ("<assign-op> ::= increase", []),
    ("<assign-op> ::= decrease", []),
    ("<durative-action-def> ::= (:durative-action <da-symbol> :parameters (<typed list (variable)>) <da-def body>)", []),
    ("<da-symbol> ::= <name>", []),
    ("<da-def body> ::= :duration <duration-constraint> :condition <emptyOr (da-GD)> :effect <emptyOr (da-effect)>", []),
    ("<da-GD> ::= <pref-timed-GD>", []),
    ("<da-GD> ::= (and <da-GD>*)", []),
    ("<da-GD> ::= (forall (<typed-list (variable)>) <da-GD>)", ["universal−preconditions"]),
    ("<pref-timed-GD> ::= <timed-GD>", []),
    ("<pref-timed-GD> ::= (preference [<pref-name>] <timed-GD>)", ["preferences"]),
    ("<timed-GD> ::= (at <time-specifier> <GD>)", []),
    ("<timed-GD> ::= (over <interval> <GD>)", []),
    ("<time-specifier> ::= start", []),
    ("<time-specifier> ::= end", []),
    ("<interval> ::= all", []),
    ("<duration-constraint> ::= (and <simple-duration-constraint>+)", ["duration−inequalities"]),
    ("<duration-constraint> ::= ()", []),
    ("<duration-constraint> ::= <simple-duration-constraint>", []),
    ("<simple-duration-constraint> ::= (<d-op> ?duration <d-value>)", []),
    ("<simple-duration-constraint> ::= (at <time-specifier> <simple-duration-constraint>)", []),
    ("<d-op> ::= <=", ["duration−inequalities"]),
    ("<d-op> ::= >=", ["duration−inequalities"]),
    ("<d-op> ::= =", []),
    ("<d-value> ::= <number>", []),
    ("<d-value> ::= ?duration", ["duration−inequalities"]),
    ("<d-value> ::= <f-exp>", []),
    ("<da-effect> ::= (and <da-effect>*)", []),
    ("<da-effect> ::= <timed-effect>", []),
    ("<da-effect> ::= (forall (<typed list (variable)>) <da-effect>)", ["conditional−effects"]),
    ("<da-effect> ::= (when <da-GD> <timed-effect>)", ["conditional−effects"]),
    ("<timed-effect> ::= (at <time-specifier> <cond-effect>)", []),
    ("<timed-effect> ::= (at <time-specifier> <f-assign-da>)", ["numeric-fluents"]),
    ("<timed-effect> ::= (<assign-op-t> <f-head> <f-exp-t>)", ["continuous−effects", "numeric-fluents"]),
    ("<f-assign-da> ::= (<assign-op> <f-head> <f-exp-da>)", []),
    ("<f-exp-da> ::= (<binary-op> <f-exp-da> <f-exp-da>)", []),
    ("<f-exp-da> ::= (<multi-op> <f-exp-da> <f-exp-da>+)", []),
    ("<f-exp-da> ::= (- <f-exp-da>)", []),
    ("<f-exp-da> ::= ?duration", ["duration−inequalities"]),
    ("<f-exp-da> ::= <f-exp>", []),
    ("<assign-op-t> ::= increase", []),
    ("<assign-op-t> ::= decrease", []),
    ("<f-exp-t> ::= (* <f-exp> #t)", []),
    ("<f-exp-t> ::= (* #t <f-exp>)", []),
    ("<f-exp-t> ::= #t", []),
    ("<derived-def> ::= (:derived <atomic formula skeleton> <GD>)", [])
]

enabled = ["typing"]

print(filter_rules_by_requirements(PDDL_PROBLEM_BNF, enabled))
