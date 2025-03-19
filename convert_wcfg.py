import argparse

def parse_wcfg(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    graph = {}
    
    for line in lines:
        line = line.strip()
        start, rule_weight = line.split('->')
        start = start.strip()
        rule, weight = rule_weight.split('[')
        rule = rule.strip()
        weight = weight.split(']')[0]
        weight = weight.strip()

        if start not in graph.keys():
            graph[start] = {}

        graph[start][rule] = int(weight)

    return graph


def to_chomsky_normal_form(graph):
    # modifies the graph such that it changes it to a chomsky normal form
    cn_graph = {}
    for key in graph.keys():
        cn_graph[key] = {}

        for i, rule_weight in enumerate(graph[key].items()):
            rule, weight = rule_weight
            expansion = rule.split(' ')

            # if it is already chomsky normal, ignore it
            if len(expansion) <= 2:
                cn_graph[key][rule] = weight
                continue

            # j = 0 is a special case
            next_key = f'{key}_{i}_0'
            cn_graph[key][f'{expansion[0]} {next_key}'] = weight

            for j in range(1, len(expansion) - 2):
                temp_key = f'{key}_{i}_{j}'
                cn_graph[next_key] = {f'{expansion[j]} {temp_key}' : 1}
                next_key = temp_key

            # j = len(expansion) - 1 is also a speical case
            cn_graph[next_key] = {
                f'{expansion[len(expansion) - 2]} {expansion[len(expansion) - 1]}' : 1
            }

    return cn_graph


def get_total_weights(graph):
    total_weights = {}
    for key in graph.keys():
        total_weights[key] = sum(weight for _, weight in graph[key].items())
    return total_weights
    

def clean_graph(graph, input_sentence):
    # given a certain graph, this function cleans it by looking at literals not in the given sentence
    # and then eliminates any rules that directly correspond with creating that literal
    # check if the rule is indeed a literal
    for key in graph.keys():
        literals_to_del = []
        for rule in graph[key].keys():
            is_literal = (rule.strip("'") != rule or rule.strip('"')) and len(rule.split(' ')) == 1
            is_literal_rule_in_input_sentence = (
                rule.strip("'") in input_sentence.split(' ') or
                rule.strip('"') in input_sentence.split(' ')
            )

            # do nothing to literals in the graph
            if not is_literal or (is_literal and is_literal_rule_in_input_sentence):
                continue

            # otherwise, we want to:
            # 1) remove all instances of this current weight and rule to eliminate
            # 2) remove all instances where other rules lead to this current rule
            literals_to_del.append(rule)
        
        # now delete the literals from this graph[key]
        for literal in literals_to_del:
            graph[key].pop(literal)

    return graph


def output_pcfg(graph, output, total_weights):
    with open(output, 'w') as file:
        for key in graph.keys():
            for rule, weight in graph[key].items():
                sentence = f'{weight} / {total_weights[key]} {key} --> {rule}\n'
                file.write(sentence)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('-s', '--sentence')
    args = parser.parse_args()

    graph = parse_wcfg(args.input)
    graph = to_chomsky_normal_form(graph)
    # next, we need to get the total weights before cleaning
    total_weights = get_total_weights(graph)
    if args.sentence:
        graph = clean_graph(graph, args.sentence)

    output_pcfg(graph, args.output, total_weights)
