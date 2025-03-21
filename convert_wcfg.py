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

    # next, we need to get the total weights before cleaning
    total_weights = get_total_weights(graph)

    output_pcfg(graph, args.output, total_weights)
