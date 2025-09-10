#!/usr/bin/env python3
import urwid
import random
import re
from openai import OpenAI

# Embedded API key
API_KEY = ""

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

class WordGeneratorApp:
    def __init__(self):
        self.current_words = []
        self.generated_words = []
        self.selected_words = []
        self.expanded_list = []
    
    #Generate 10 related words for a given word using OpenAI API.
    def get_related_words(self, word):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates related words. Respond with exactly 10 words separated by commas, nothing else."},
                    {"role": "user", "content": f"Give me 10 words that are related to or associated with '{word}'. Only return the words separated by commas, no other text."}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            related_text = response.choices[0].message.content.strip()
            
            # Parse the response and clean up the words
            related_words = [word.strip() for word in re.split(r'[,\n]', related_text) if word.strip()]
            # Take only first 10 words and filter out any that might be phrases
            related_words = [word for word in related_words[:10] if len(word.split()) == 1 and word.isalpha()]
            return related_words[:10]  # Ensure we return at most 10 words
            
        except Exception as e:
            print(f"Error generating words for '{word}': {e}")
            return []
    
    #Expand the list to 100 words by adding related words.
    def expand_word_list(self, input_words):
        related_words = []
        
        # Generate related words for each input word
        for word in input_words:
            related_words.extend(self.get_related_words(word))
        
        # Start with input words
        expanded_list = input_words[:]
        
        # Add random words from the related words until we reach 100 or run out
        remaining_words = [word for word in related_words if word.lower() not in [w.lower() for w in expanded_list]]
        
        while len(expanded_list) < 100 and remaining_words:
            word = random.choice(remaining_words)
            remaining_words.remove(word)
            expanded_list.append(word)
        
        return expanded_list
    
    #Get initial words from user input.
    def get_user_input(self):
        print("Word Generator App")
        print("=" * 50)
        user_input = input("Enter up to 10 words (separated by spaces or commas): ").strip()
        
        if not user_input:
            return []
            
        # Parse input: split by spaces and commas, clean up
        words = re.split(r'[,\s]+', user_input)
        words = [word.strip().lower() for word in words if word.strip().isalpha()]
        
        # Take only first 10 words
        return words[:10]
    
    #Create the word selection interface using urwid.
    def create_selection_interface(self, words):
        # Create checkbox widgets for each word
        self.checkboxes = []
        body = []
        
        for word in words:
            checkbox = urwid.CheckBox(word)
            self.checkboxes.append(checkbox)
            body.append(urwid.AttrMap(checkbox, None, focus_map='reversed'))
        
        # Add instructions at the top
        instructions = [
            urwid.Text("Select up to 10 words using SPACE or mouse clicks then press ESC to close:"),
            urwid.Divider()
        ]
        
        # Create the list walker and list box
        walker = urwid.SimpleFocusListWalker(instructions + body)
        listbox = urwid.ListBox(walker)
        
        # Create the main widget
        return urwid.Frame(urwid.AttrWrap(listbox, 'body'))
    
    #Handle key presses.
    def unhandled_input(self, key):
        if key == 'esc':
            selected = [cb for cb in self.checkboxes if cb.get_state()]
            self.selected_words = [cb.get_label() for cb in selected][:10]
            raise urwid.ExitMainLoop()
    
    #Run the word selection interface.
    def run_selection(self, words):
        main_widget = self.create_selection_interface(words)
        
        # Define color palette
        palette = [
            ('body', 'default', 'default'),
            ('header', 'white', 'dark blue', 'bold'),
            ('footer', 'white', 'dark green'),
            ('error', 'white', 'dark red'),
            ('reversed', 'standout', ''),
        ]
        
        # Create and run the main loop
        self.loop = urwid.MainLoop(
            main_widget, 
            palette, 
            unhandled_input=self.unhandled_input,
            handle_mouse=True
        )
        
        try:
            self.loop.run()
        except urwid.ExitMainLoop:
            pass
    
    #Main application loop.
    def run(self):
        # Get initial words from user
        self.current_words = self.get_user_input()
        
        if not self.current_words:
            print("No valid words entered. Exiting.")
            return
        
        while True:
            # Generate and expand word list
            print("\nGenerating related words...")
            self.expanded_list = self.expand_word_list(self.current_words)
            
            # Show word selection interface
            self.run_selection(self.expanded_list)
            
            # Check if user made selections
            if not self.selected_words:
                print("\nNo more words selected. Exiting...")
                print(f"Picked words: {', '.join(self.current_words)}")
                break
            
            # Update current words for next iteration
            self.current_words = self.selected_words
            self.selected_words = []

try:
    WordGeneratorApp().run()
except KeyboardInterrupt:
    print("\n\nApplication interrupted by user. Goodbye!")
except Exception as e:
    print(f"\nAn error occurred: {e}")
