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
            graph[start] = []

        graph[start].append((int(weight), rule))

    return graph


def to_chomsky_normal_form(graph):
    # modifies the graph such that it changes it to a chomsky normal form
    cn_graph = {}
    for key in graph.keys():
        cn_graph[key] = []

        for i, rule_weight in enumerate(graph[key]):
            weight, rule = rule_weight
            expansion = rule.split(' ')

            # if it is already chomsky normal, ignore it
            if len(expansion) <= 2:
                cn_graph[key].append(rule_weight)
                continue

            # j = 0 is a special case
            next_key = f'{key}_{i}_0'
            cn_graph[key].append((weight, f'{expansion[0]} {next_key}'))

            for j in range(1, len(expansion) - 2):
                temp_key = f'{key}_{i}_{j}'
                cn_graph[next_key] = [(1, f'{expansion[j]} {temp_key}')]
                next_key = temp_key

            # j = len(expansion) - 1 is also a speical case
            cn_graph[next_key] = [(1, f'{expansion[len(expansion) - 2]} {expansion[len(expansion) - 1]}')]

    return cn_graph



def output_pcfg(graph, output):
    with open(output, 'w') as file:
        for key in graph.keys():
            total_weight = sum(weight for weight, _ in graph[key])
            for weight, rule in graph[key]:
                sentence = f'{weight} / {total_weight} {key} --> {rule}\n'
                file.write(sentence)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    graph = parse_wcfg(args.input)
    graph = to_chomsky_normal_form(graph)
    output_pcfg(graph, args.output)
