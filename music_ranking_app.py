import streamlit as st
import random
import statistics
from streamlit_sortables import sort_items

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

def small_batch_ranking(songs, group_size=5, max_rounds=20, confidence_threshold=0.9):
    """
    Rank songs using small-batch comparisons with adaptive sampling and confidence-based stopping.
    """
    # Initialize scores and uncertainties
    scores = {song: 0 for song in songs}
    uncertainties = {song: float('inf') for song in songs}
    history = {song: [] for song in songs}  # To track score history for variance calculation
    
    for round_num in range(max_rounds):
        st.write(f"--- Round {round_num + 1} ---")
        
        # Adaptive sampling: Prioritize songs with high uncertainty or close scores
        sorted_songs = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        groups = []
        
        for i in range(0, len(sorted_songs), group_size):
            group = sorted_songs[i:i + group_size]
            # Shuffle to mix high-uncertainty and close-scored songs
            random.shuffle(group)
            groups.append(group)
        
        # Simulate user rankings for each group
        for group in groups:
            st.write("Rank these songs from best to worst:")
            
            # Use streamlit_sortables for drag-and-drop ranking
            ranked_group = sort_items(group)
            
            # Update scores using Borda count
            for i, song in enumerate(ranked_group):
                scores[song] += (group_size - i)  # Higher rank = more points
            
            # Track score changes for uncertainty calculation
            for song in group:
                history[song].append(scores[song])
        
        # Update uncertainties based on score variance
        for song in songs:
            if len(history[song]) > 1:
                uncertainties[song] = statistics.variance(history[song])
            else:
                uncertainties[song] = float('inf')
        
        # Check confidence threshold
        avg_confidence = sum(1 / (uncertainties[song] + 1e-6) for song in songs) / len(songs)
        st.write(f"Round {round_num + 1}: Average Confidence = {avg_confidence:.2f}")
        if avg_confidence >= confidence_threshold:
            st.write(f"Stopping early at round {round_num + 1} due to high confidence.")
            break
    
    # Final ranking based on scores
    final_ranking = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return final_ranking, scores, uncertainties

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
        st.write("Let's get started! Please rank the songs in each group.")
        
        # Run the ranking algorithm
        ranking, scores, uncertainties = small_batch_ranking(
            songs,
            group_size=group_size,
            max_rounds=20,
            confidence_threshold=0.9
        )
        
        if ranking:
            st.write("\n🎉 **Final Ranking:** 🎉")
            for i, song in enumerate(ranking, start=1):
                st.write(f"{i}. {song} (Score: {scores[song]:.2f}, Uncertainty: {uncertainties[song]:.2f})")

if __name__ == "__main__":
    main()
