from dialogy.plugin import Plugin, PluginFn
from typing import Optional


def count_matching_entities(ent, all_ents):
    """
    Counts the number of entities with same type and value.
    """
    count = 0
    for t_e in all_ents:
        if ent.type == t_e.type:
            if ent.value == t_e.value:
                count += 1
    return count


class RemoveSingleAlternatives(Plugin):

    """
    Removes the less confident entities from the duckling output.
    
    If your transcripts look like ("22 May", "Tu May", "2 May", "Two May", "2 May"). Duckling Parser output will be 22 May and 2 May. This plugin will ensure you dont't fill 22 May in slots
    as it was a less confident entity.

    Usage: 
        def update_entities_new(workflow, entities):
            workflow.output= (workflow.output[0], entities)

        remove_single_alternative_plugin=RemoveSingleAlternatives(access=lambda w: (w.input[const.S_CLASSIFICATION_INPUT], w.output[0], w.output[1], w.input[const.S_CONTEXT]), mutate= update_entities)()
        
        **Use this plugin after duckling parser in your preprocessors list.**     
    """


    def __init__(
        self,
        access: Optional[PluginFn],
        mutate: Optional[PluginFn]
    ) -> None:
        
        super().__init__(access=access, mutate=mutate)


    def removing_logic(self, alternatives, entities):
        """
        Dialogy equivalent of remove_single_alternative_ent mutator
        """
        alternatives = alternatives.replace("<s> ", "")
        alternatives = alternatives.split(" </s>")
        alternatives_list = alternatives
        
        # if there are less than 4 alternatives than we don't remove any entities
        if len(alternatives_list) < 4:
            return entities

        non_singular_ents = []
        for ent in entities:
            if count_matching_entities(ent, entities) > 1:
                non_singular_ents.append(ent)

        return non_singular_ents
        

    def plugin(self, workflow) -> None:
        """
        Plugin to ease workflow io.
        """
        access = self.access
        mutate = self.mutate
        if access and mutate:
            alternatives, entities = access(workflow)
            updated_entities = self.removing_logic(alternatives, entities)
            mutate(workflow, updated_entities)
        else:
            raise TypeError(
                "Expected `access` and `mutate` to be Callable,"
                f" got access={type(access)} mutate={type(mutate)}"
            )

    def __call__(self) -> PluginFn:

        return self.plugin
