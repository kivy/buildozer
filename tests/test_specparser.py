from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from buildozer.specparser import SpecParser


class TestSpecParser(unittest.TestCase):
    def test_overrides(self):
        environ["SECTION_1_ATTRIBUTE_1"] = "Env Value"

        # Test as a string.
        sp = SpecParser()
        sp.read_string(
            """
            [section.1]
            attribute.1=String Value
            """
        )
        assert sp.get("section.1", "attribute.1") == "Env Value"

        # Test as a dict
        sp = SpecParser()
        sp.read_dict({"section.1": {"attribute.1": "Dict Value"}})
        assert sp.get("section.1", "attribute.1") == "Env Value"

        with TemporaryDirectory() as temp_dir:
            spec_path = Path(temp_dir) / "test.spec"
            with open(spec_path, "w") as spec_file:
                spec_file.write(
                    """
                    [section.1]
                    attribute.1=File Value
                    """
                )

            # Test as a file
            sp = SpecParser()
            with open(spec_path, "r") as spec_file:
                sp.read_file(spec_file)
            assert sp.get("section.1", "attribute.1") == "Env Value"

            # Test as a list of filenames
            sp = SpecParser()
            sp.read([spec_path])
            assert sp.get("section.1", "attribute.1") == "Env Value"

        del environ["SECTION_1_ATTRIBUTE_1"]

    def test_new_getters(self):
        sp = SpecParser()
        sp.read_string(
            """
                [section1]
                attribute1=1
                attribute2=red, white, blue
                attribute3=True
                attribute5=large/medium/small

                [section2:attribute4]
                red=1
                amber=
                green=3


            """
        )

        assert sp.get("section1", "attribute1") == "1"
        assert sp.getlist("section1", "attribute2") == ["red", "white", "blue"]
        assert sp.getlist("section1", "attribute2", strip=False) == [
            "red",
            " white",
            " blue",
        ]

        assert sp.getlist("section2", "attribute4") == [
            "red",
            "amber",
            "green",
        ]
        # Test with_values and section_sep
        assert sp.getlistvalues("section2", "attribute4") == [
            "red=1",
            "amber=",
            "green=3",
        ]
        assert sp.getlist(
            "section2", "attribute4", with_values=True, section_sep=":"
        ) == [
            "red:1",
            "amber:",
            "green:3",
        ]
        # Test split_char
        assert sp.getlist("section1", "attribute5", with_values=True) == [
            "large/medium/small",
        ]
        assert sp.getlist(
            "section1", "attribute5", with_values=True, split_char="/"
        ) == [
            "large",
            "medium",
            "small",
        ]

        assert sp.getbooldefault("section1", "attribute3") is True

    def test_case_sensitivity(self):
        sp = SpecParser()
        sp.read_string(
            """
                [section1]
                attribute1=a
                Attribute1=A
            """
        )

        assert sp.get("section1", "attribute1") == "a"
        assert sp.get("section1", "Attribute1") == "A"

    def test_profiles(self):
        sp = SpecParser()
        sp.read_string(
            """
                [section1]
                attribute1=full system
                [section1 @demo1, demo2]
                attribute1=demo mode
            """
        )

        # Before a profile is set, return the basic version.
        assert sp.get("section1", "attribute1") == "full system"

        # Empty profile makes no difference.
        sp.apply_profile(None)
        assert sp.get("section1", "attribute1") == "full system"

        # Inapplicable profile makes no difference
        sp.apply_profile("doesn't exist")
        assert sp.get("section1", "attribute1") == "full system"

        # Applicable profile changes value
        sp.apply_profile("demo2")
        assert sp.get("section1", "attribute1") == "demo mode"

    def test_profiles_vs_env_var(self):
        sp = SpecParser()

        environ["SECTION1_ATTRIBUTE1"] = "simulation mode"

        sp.read_string(
            """
                [section1]
                attribute1=full system
                [section1@demo1,demo2]
                attribute1=demo mode
            """
        )

        # Before a profile is set, env var should win.
        assert sp.get("section1", "attribute1") == "simulation mode"

        # Applicable profile: env var should still win
        sp.apply_profile("demo1")
        assert sp.get("section1", "attribute1") == "simulation mode"

        del environ["SECTION1_ATTRIBUTE1"]

    def test_controversial_cases(self):
        """Some aspects of the config syntax seem to cause confusion.
        This shows what the code is *specified* to do, which might not be
        expected.
        """
        sp = SpecParser()
        sp.read_string(
            """
                [section]
                    # Comments can be indented.
                option1=a  # This is not considered a comment
                option2=this is
                   a multiline string (not a list!)
                   # This is considered a comment.
                   this_is_not_an_option=it is still part of the multiline
                option3=this, is, one, way, of, representing, lists

                [section:option4]
                this_is
                another_way
                # This is a comment.
                of # This is not a comment.
                representing=4
                lists
            """
        )

        assert (
            sp.get("section", "option1") ==
            "a  # This is not considered a comment"
        )
        assert (
            sp.get("section", "option2") ==
            "this is\na multiline string (not a list!)\n"
            "this_is_not_an_option=it is still part of the multiline"
        )
        assert sp.getlist("section", "option3") == [
            "this",
            "is",
            "one",
            "way",
            "of",
            "representing",
            "lists",
        ]
        assert sp.getlist("section", "option4") == [
            "this_is",
            "another_way",
            "of # This is not a comment.",
            "representing",
            "lists",
        ]
