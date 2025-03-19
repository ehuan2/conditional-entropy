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
    output_pcfg(graph, args.output)
