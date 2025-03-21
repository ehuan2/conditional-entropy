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
            next_key = f'CNF_{key}_{i}_0'
            cn_graph[key][f'{expansion[0]} {next_key}'] = weight

            for j in range(1, len(expansion) - 2):
                temp_key = f'CNF_{key}_{i}_{j}'
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

    output_pcfg(graph, args.output, total_weights)
