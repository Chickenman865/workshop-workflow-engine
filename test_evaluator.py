from core.evaluator import evaluate_facts


rules = {
    "target_voltage_min":0.45,
    "target_voltage_max":0.55,
    "required_behavior":"stable"
}


tests = [

{
"voltage_values":[0.5],
"meter_behavior":"stable",
"user_uncertainty":False
},

{
"voltage_values":[0.2,0.8],
"meter_behavior":"jumping",
"user_uncertainty":False
},

{
"voltage_values":[],
"meter_behavior":"",
"user_uncertainty":True
}

]


for test in tests:

    state, quality = evaluate_facts(test,rules)

    print(test)
    print("RESULT:", state.value)
    print("QUALITY:", quality.model_dump())
    print("-"*40)