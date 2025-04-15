import streamlit as st
import random
import statistics

# Initialize session state
if "songs" not in st.session_state:
    st.session_state.songs = []
if "group_size" not in st.session_state:
    st.session_state.group_size = 5
if "current_group" not in st.session_state:
    st.session_state.current_group = []
if "ranked_group" not in st.session_state:
    st.session_state.ranked_group = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "uncertainties" not in st.session_state:
    st.session_state.uncertainties = {}
if "history" not in st.session_state:
    st.session_state.history = {}
if "round_num" not in st.session_state:
    st.session_state.round_num = 0
if "final_ranking" not in st.session_state:
    st.session_state.final_ranking = None
if "groups" not in st.session_state:  # Ensure groups are initialized
    st.session_state.groups = []
if "current_group_index" not in st.session_state:  # Ensure current_group_index is initialized
    st.session_state.current_group_index = 0

# Default list of 10 random songs for aesthetics
DEFAULT_SONGS = [
    "Bohemian Rhapsody - Queen",
    "Stairway to Heaven - Led Zeppelin",
    "Hotel California - Eagles",
    "Imagine - John Lennon",
    "Like a Rolling Stone - Bob Dylan",
    "Smells Like Teen Spirit - Nirvana",
    "Hey Jude - The Beatles",
    "Sweet Child O' Mine - Guns N' Roses",
    "I Want to Hold Your Hand - The Beatles",
    "Purple Haze - Jimi Hendrix"
]

def initialize_ranking(songs, group_size):
    """
    Initialize the ranking process by setting up groups and scores.
    """
    st.session_state.songs = songs
    st.session_state.group_size = group_size
    st.session_state.scores = {song: 0 for song in songs}
    st.session_state.uncertainties = {song: float('inf') for song in songs}
    st.session_state.history = {song: [] for song in songs}
    st.session_state.round_num = 0
    st.session_state.final_ranking = None

    # Split songs into groups
    random.shuffle(st.session_state.songs)
    st.session_state.groups = [
        st.session_state.songs[i:i + group_size]
        for i in range(0, len(st.session_state.songs), group_size)
    ]
    st.session_state.current_group_index = 0
    st.session_state.current_group = st.session_state.groups[st.session_state.current_group_index].copy()
    st.session_state.ranked_group = []

def rank_songs():
    """
    Rank songs using small-batch comparisons with adaptive sampling and confidence-based stopping.
    """
    if st.session_state.final_ranking:
        return st.session_state.final_ranking

    # If the current group is fully ranked, move to the next group
    if not st.session_state.current_group and st.session_state.current_group_index < len(st.session_state.groups) - 1:
        # Update scores for the ranked group
        for i, song in enumerate(st.session_state.ranked_group):
            st.session_state.scores[song] += (st.session_state.group_size - i)
            st.session_state.history[song].append(st.session_state.scores[song])
        
        # Move to the next group
        st.session_state.current_group_index += 1
        st.session_state.current_group = st.session_state.groups[st.session_state.current_group_index].copy()
        st.session_state.ranked_group = []

    # If all groups are ranked, update uncertainties and check confidence
    if not st.session_state.current_group and st.session_state.current_group_index == len(st.session_state.groups) - 1:
        # Update uncertainties based on score variance
        for song in st.session_state.songs:
            if len(st.session_state.history[song]) > 1:
                st.session_state.uncertainties[song] = statistics.variance(st.session_state.history[song])
            else:
                st.session_state.uncertainties[song] = float('inf')
        
        # Check confidence threshold
        avg_confidence = sum(1 / (st.session_state.uncertainties[song] + 1e-6) for song in st.session_state.songs) / len(st.session_state.songs)
        st.write(f"Round {st.session_state.round_num + 1}: Average Confidence = {avg_confidence:.2f}")
        if avg_confidence >= 0.9 or st.session_state.round_num >= 19:
            st.session_state.final_ranking = sorted(
                st.session_state.scores.keys(),
                key=lambda x: st.session_state.scores[x],
                reverse=True
            )
            return st.session_state.final_ranking
        
        # Start a new round
        st.session_state.round_num += 1
        random.shuffle(st.session_state.songs)
        st.session_state.groups = [
            st.session_state.songs[i:i + st.session_state.group_size]
            for i in range(0, len(st.session_state.songs), st.session_state.group_size)
        ]
        st.session_state.current_group_index = 0
        st.session_state.current_group = st.session_state.groups[st.session_state.current_group_index].copy()
        st.session_state.ranked_group = []

    return None

# Streamlit App
def main():
    st.title("🎵 Music Ranking App 🎵")
    st.write("This app ranks your favorite songs using small-batch comparisons!")

    # Input: Number of songs
    n = st.number_input("Enter the number of songs to rank:", min_value=2, value=10, step=1)

    # Use default songs if n <= 10, otherwise generate random song names
    if n <= 10:
        songs = DEFAULT_SONGS[:n]
    else:
        songs = [f"Song{i+1}" for i in range(n)]

    # Display the list of songs
    st.write("**Songs to Rank:**")
    st.write(songs)

    # Input: Group size
    group_size = st.number_input("Enter the group size for comparisons:", min_value=2, value=5, step=1)

    # Start ranking process
    if st.button("Start Ranking"):
        initialize_ranking(songs, group_size)
        st.write("Let's get started! Please rank the songs in each group.")

    # Run the ranking algorithm
    if not st.session_state.final_ranking:
        rank_songs()

    # Display current group for ranking
    if st.session_state.current_group:
        st.write(f"Rank these songs from best to worst:")
        selected_song = st.selectbox(
            f"Select your favorite song from the group: {st.session_state.current_group}",
            options=st.session_state.current_group
        )
        if st.button("Submit Selection"):
            st.session_state.ranked_group.append(selected_song)
            st.session_state.current_group.remove(selected_song)

    # Display final results
    if st.session_state.final_ranking:
        st.write("\n🎉 **Final Ranking:** 🎉")
        for i, song in enumerate(st.session_state.final_ranking, start=1):
            st.write(f"{i}. {song} (Score: {st.session_state.scores[song]:.2f}, Uncertainty: {st.session_state.uncertainties[song]:.2f})")

if __name__ == "__main__":
    main()
