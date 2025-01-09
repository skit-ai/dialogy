import json
import pytest
import pandas as pd

from dialogy.base import Guard, Input, Output
from dialogy.plugins.registry import TransliterationPlugin
from dialogy.workflow import Workflow

# Initialize plugin instance for testing
transliteration_plugin = TransliterationPlugin(
    dest = "input.utterances",
    guards = [(lambda i, o, _: i.lang == "en")]
)

@pytest.mark.asyncio
async def test_basic_transliteration():
    """
    Test basic transliteration of English date/time words to Hindi
    """
    workflow = Workflow([transliteration_plugin])
    input_ = Input(utterances=[[{"transcript": "monday को meeting है"}]], lang="hi")
    
    input_, _ = await workflow.run(input_)
    assert input_.utterances[0][0]["transcript"] == "सोमवार को meeting है"

@pytest.mark.asyncio
async def test_guard_blocks_transliteration():
    """
    Test that guard blocks transliteration when lang is 'en'
    """
    workflow = Workflow([transliteration_plugin])
    input_ = Input(utterances=[[{"transcript": "monday को meeting है"}]], lang="en")
    
    input_, _ = await workflow.run(input_)
    # Should remain unchanged since guard blocks transliteration for lang="en"
    assert input_.utterances[0][0]["transcript"] == "monday को meeting है"

@pytest.mark.asyncio
async def test_multiple_datetime_words():
    """
    Test transliteration of multiple date/time words in a sentence
    """
    workflow = Workflow([transliteration_plugin])
    input_ = Input(utterances=[[{
        "transcript": "next monday morning meeting रखें"
    }]], lang="hi")
    
    input_, _ = await workflow.run(input_)
    assert input_.utterances[0][0]["transcript"] == "अगला सोमवार सुबह meeting रखें"

@pytest.mark.asyncio
async def test_case_insensitive():
    """
    Test that transliteration is case-insensitive
    """
    workflow = Workflow([transliteration_plugin])
    input_ = Input(utterances=[[{
        "transcript": "MONDAY को या Tuesday को"
    }]], lang="hi")
    
    input_, _ = await workflow.run(input_)
    assert input_.utterances[0][0]["transcript"] == "सोमवार को या मंगलवार को"

@pytest.mark.asyncio
async def test_empty_utterances():
    """
    Test handling of empty utterances
    """
    workflow = Workflow([transliteration_plugin])
    input_ = Input(utterances=[[]], lang="hi")
    
    input_, _ = await workflow.run(input_)
    assert input_.utterances == [[]]

@pytest.mark.asyncio
async def test_no_datetime_words():
    """
    Test that non-datetime words remain unchanged
    """
    workflow = Workflow([transliteration_plugin])
    original = "मैं office जा रहा हूं"
    input_ = Input(utterances=[[{"transcript": original}]], lang="hi")
    
    input_, _ = await workflow.run(input_)
    assert input_.utterances[0][0]["transcript"] == original

@pytest.mark.asyncio
async def test_multiple_alternatives():
    """
    Test handling of multiple transcript alternatives
    """
    workflow = Workflow([transliteration_plugin])
    input_ = Input(utterances=[[
        {"transcript": "monday को meeting"},
        {"transcript": "tuesday को meeting"}
    ]], lang="hi")
    
    input_, _ = await workflow.run(input_)
    assert input_.utterances[0][0]["transcript"] == "सोमवार को meeting"
    assert input_.utterances[0][1]["transcript"] == "मंगलवार को meeting"

@pytest.mark.asyncio
async def test_punctuation_handling():
    """
    Test that punctuation is handled correctly
    """
    workflow = Workflow([transliteration_plugin])
    input_ = Input(utterances=[[{
        "transcript": "monday, tuesday और wednesday!"
    }]], lang="hi")
    
    input_, _ = await workflow.run(input_)
    assert input_.utterances[0][0]["transcript"] == "सोमवार मंगलवार और बुधवार"
