import loaders
import os
import unicodedata
import json


show_extra_data = False
flattened_output = True


# see: https://stackoverflow.com/questions/4324790
def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

class CategoryMatcher:
    def __init__(self, obj, name=''):
        self.fields = {}
        self.optionals = set()
        self.name = name
        self.children = {}
        self.values = {}
        for key, value in obj.items():
            self.fields[key] = type(value)
            self.add_or_update_children(key, value)
            self.add_or_update_value(key, value)

        #if type(value) == type(None):
        #    self.optionals.add(key)

    def add_or_update_value(self, key, value):
        if type(value) in [bool, str, int, float]:
            self.values[key] = self.values.get(key, []) + [value]
        elif type(value) == list:
            for v in value:
                self.add_or_update_value(key, v)



    def add_or_update_children(self, key, value):
        if type(value) not in [dict, list]:
            # We don't deal with non-complex datatypes
            return None

        self.children[key] = self.children.get(key, [])
        if type(value) == dict:
            matched = False
            for matcher in self.children[key]:
                if matcher.matches(value):
                    matched = True
                    break
            if not matched:
                self.children[key].append(CategoryMatcher(value, name=key))
        elif type(value) == list and set(map(type, value)) == set([dict]):
            for v in value:
                matched = False
                for matcher in self.children[key]:
                    if matcher.matches(v):
                        matched = True
                        break
                if not matched:
                    self.children[key].append(CategoryMatcher(v, name=key))


    def matches(self, obj):
        optionals_found = set()
        types_found = {}
        for key, value in obj.items():
            if key not in self.fields:
                # If is a key we don't have, it isn't of our category
                # print("Don't has field {}".format(key))
                return False
            elif type(value) == type(None) and self.fields[key] != type(None):
                # If is a key we have, but is empty, it MAY BE an optional key
                # NoneType keys, however, can't be optional (they're empty)
                optionals_found.add(key)
            elif self.fields[key] == type(None):
                # We know this field is optional, but we don't know its type yet
                types_found[key] = type(value)
            elif self.fields[key] == int and type(value) == float:
                # Float is a superset of int, so we need caution
                types_found[key] = float
            elif type(value) != self.fields[key]:
                # If is a key we have, but the type don't match, it isn't ours
                print("Field {} is {} instead of {}"
                      .format(key, type(value).__name__, self.fields[key].__name__))
                return False
        # If every test passed, then it is in ours category
        # It also may contribute to our knowledge of what our category is
        self.optionals = self.optionals.union(optionals_found)
        for key, value in types_found.items():
            if self.fields[key] == type(None) and value != type(None):
                self.fields[key] = value
                if type(value) == dict:
                    self.children[key] = [CategoryMatcher(value, name=key)]

            if key not in self.fields:
                self.fields[key] = value

                if value in [dict, list]:
                    self.children[key] = []


        for key, value in obj.items():
            if self.fields[key] in [dict, list]:
                self.add_or_update_children(key, value)
            self.add_or_update_value(key, value)
        return True

    def __str__(self):
        string = '{"CategoryMatcher":'
        string += ' "{}",'.format(self.name)
        string += ' "size": {},'.format(len(self.fields))

        if "CategoryMatcher" in self.fields:
            del self.fields["CategoryMatcher"]

        field_strings = []
        for field, value in self.fields.items():
            field_string = '"{}'.format(field)
            if field in self.optionals:
                field_string += ' (optional)'
            else:
                field_string += ''

            if value not in [dict, list]:
                field_string += '": "{}'.format(value.__name__)

                # if field in self.values:
                #     print([len(self.values[field]), len(set(self.values[field]))])

                if (field in self.values
                    and len(self.values[field]) > len(set(self.values[field]))
                    and show_extra_data):
                    field_string += (' [{}]"'
                                     .format(', '.join([remove_control_characters('\\"{}\\"'
                                                                                  .format(str(x)
                                                                                          .replace('"', '\\"')
                                                                                          .replace('\n', '\\n')
                                                                                          .replace('\r', '\\r')
                                                                                          .replace('\b', '\\b')))
                                                        for x in set(self.values[field])])))
                else:
                    field_string += '"'
            else:
                if field in self.children:
                    field_string += '": [{}]'.format(", ".join(map(str, self.children[field])))
                else:
                    field_string += '": []'

            field_strings.append(field_string)

        field_strings.sort(key=lambda x: ("1" + x) if "optional" in x else ("0" + x))
        return string + " " + ", ".join(field_strings) + "}"

    def __repr__(self):
        return self.__str__()

matchers = []

for filepath in loaders.FindSSFile('.json', listmode=True):
    filename = os.path.split(filepath)[-1]
    if filename in ["config.json"]:
        continue
#    print(filename)

    for obj in loaders.ObjectsFromJsonFile(filename):
        if not any(map(lambda matcher: matcher.matches(obj), matchers)):
            matchers.append(CategoryMatcher(obj, name=filename))

json_metadata = "[{}]".format(", ".join([str(x) for x in matchers]))

if not flattened_output:
    print(json_metadata)

import functools

def flatten_and_typesample_dicts(obj):
    #print("obj is {}".format(obj))
    #print(type(obj))
    if type(obj) == type(type(0)):
        return [obj]
    elif type(obj) == type(None):
        return []
    elif type(obj) == list:
        return functools.reduce(lambda x, y: (x + flatten_and_typesample_dicts(y)), obj, [])

    else: # It's a ddict!
        my_obj = {}

        # Typesampling
        for key, value in list(obj.items()):
            #print((key, value))
            if type(value) != str: # Probable complex type, like dict and lists
                my_obj[key] = value
                continue

            if key in ["CategoryMatcher", "size"]:
                my_obj[key] = value
            elif "str" in value:
                my_obj[key] = str()
            elif "bool" in value:
                my_obj[key] = bool()
            elif "int" in value:
                my_obj[key] = 0
            elif "float" in value:
                my_obj[key] = 0.1
            elif "NoneType" in value:
                my_obj[key] = None
            else: # Probable complex type, like dict and lists
                my_obj[key] = value

        #print("my_obj is {}".format(my_obj))
        complex_children = []

        #print('-'*80)
        for key, value in list(my_obj.items()):
            #print((key, value))
            if type(value) in [dict, list]:
                #print((key, value))
                r = flatten_and_typesample_dicts(value)
                #print(r)
                complex_children.extend(r)
                del my_obj[key]

        #print("complex_children is {}".format(complex_children))
        #print('='*80)
        #print("my_obj is {}".format(my_obj))
        return (complex_children + [my_obj])


def pprint(obj):
    if type(obj) == str:
        json_str = json.loads(obj)
    else:
        json_str = obj
    print(json.dumps(json_str, indent=4, sort_keys=True))

if not show_extra_data and flattened_output:
    #print(len(json_metadata))
    objs = json.loads(json_metadata)
    #print(objs)

    metamatchers = []
    flatted = flatten_and_typesample_dicts(objs)
    flatted.sort(key=lambda x: ('1' + str(x)) if '.json' in x["CategoryMatcher"] else ('0' + str(x)))
    #[pprint(x) for x in flatted]
    #print(json.dumps(flatted))

    for obj in flatted:
        #[pprint(str(m)) for m in metamatchers]
        #print('-'*80)
        if not any(map(lambda m: m.matches(obj), metamatchers)):
            metamatchers.append(CategoryMatcher(obj, name=obj["CategoryMatcher"]))

    json_metametadata = "[{}]".format(", ".join([str(x) for x in metamatchers]))

    pprint(json_metametadata)

    # patts = find_patterns_in_string(json_metadata, 200, 320, 40)
    # for patt, qtd in patts.items():
    #     if qtd > 2:
    #         print("{}: {}").format(qtd, patt)
