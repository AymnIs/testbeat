import streamlit as st
import random
import statistics

# Initialize session state
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
    # Initialize scores and uncertainties (only on first run)
    if not st.session_state.scores:
        st.session_state.scores = {song: 0 for song in songs}
    if not st.session_state.uncertainties:
        st.session_state.uncertainties = {song: float('inf') for song in songs}
    if not st.session_state.history:
        st.session_state.history = {song: [] for song in songs}

    # Stop if final ranking is already calculated
    if st.session_state.final_ranking:
        return st.session_state.final_ranking

    # Adaptive sampling: Prioritize songs with high uncertainty or close scores
    sorted_songs = sorted(st.session_state.scores.keys(), key=lambda x: st.session_state.scores[x], reverse=True)
    groups = []

    for i in range(0, len(sorted_songs), group_size):
        group = sorted_songs[i:i + group_size]
        # Shuffle to mix high-uncertainty and close-scored songs
        random.shuffle(group)
        groups.append(group)

    # Simulate user rankings for each group
    for group in groups:
        st.write("Rank these songs from best to worst:")
        
        # Use a drag-and-drop HTML widget
        html_content = f"""
        <div id="sortable-list">
            {''.join([f'<div class="item" draggable="true">{song}</div>' for song in group])}
        </div>
        <script>
            const items = document.querySelectorAll('.item');
            items.forEach(item => {{
                item.addEventListener('dragstart', () => {{
                    setTimeout(() => item.classList.add('dragging'), 0);
                }});
                item.addEventListener('dragend', () => item.classList.remove('dragging'));
            }});
            const list = document.querySelector('#sortable-list');
            list.addEventListener('dragover', e => {{
                e.preventDefault();
                const dragging = document.querySelector('.dragging');
                const afterElement = getDragAfterElement(list, e.clientY);
                if (afterElement == null) {{
                    list.appendChild(dragging);
                }} else {{
                    list.insertBefore(dragging, afterElement);
                }}
            }});
            function getDragAfterElement(container, y) {{
                const draggableElements = [...container.querySelectorAll('.item:not(.dragging)')];
                return draggableElements.reduce((closest, child) => {{
                    const box = child.getBoundingClientRect();
                    const offset = y - box.top - box.height / 2;
                    if (offset < 0 && offset > closest.offset) {{
                        return {{ offset: offset, element: child }};
                    }} else {{
                        return closest;
                    }}
                }}, {{ offset: Number.NEGATIVE_INFINITY }}).element;
            }}
        </script>
        """
        st.components.v1.html(html_content, height=300)
        
        # Get ranked order from user input
        ranked_group = st.text_input(f"Enter the ranked order of songs (comma-separated):", value=",".join(group))
        ranked_group = [song.strip() for song in ranked_group.split(",") if song.strip()]
        
        # Update scores using Borda count
        for i, song in enumerate(ranked_group):
            st.session_state.scores[song] += (group_size - i)  # Higher rank = more points
        
        # Track score changes for uncertainty calculation
        for song in group:
            st.session_state.history[song].append(st.session_state.scores[song])
    
    # Update uncertainties based on score variance
    for song in songs:
        if len(st.session_state.history[song]) > 1:
            st.session_state.uncertainties[song] = statistics.variance(st.session_state.history[song])
        else:
            st.session_state.uncertainties[song] = float('inf')
    
    # Check confidence threshold
    avg_confidence = sum(1 / (st.session_state.uncertainties[song] + 1e-6) for song in songs) / len(songs)
    st.write(f"Round {st.session_state.round_num + 1}: Average Confidence = {avg_confidence:.2f}")
    if avg_confidence >= confidence_threshold:
        st.write(f"Stopping early at round {st.session_state.round_num + 1} due to high confidence.")
        st.session_state.final_ranking = sorted(st.session_state.scores.keys(), key=lambda x: st.session_state.scores[x], reverse=True)
        return st.session_state.final_ranking
    
    # Increment round number
    st.session_state.round_num += 1
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
        st.session_state.round_num = 0
        st.session_state.final_ranking = None
        st.session_state.scores = {song: 0 for song in songs}
        st.session_state.uncertainties = {song: float('inf') for song in songs}
        st.session_state.history = {song: [] for song in songs}
        st.write("Let's get started! Please rank the songs in each group.")
    
    # Run the ranking algorithm
    if st.session_state.final_ranking is None and st.session_state.round_num < 20:
        final_ranking = small_batch_ranking(
            songs,
            group_size=group_size,
            max_rounds=20,
            confidence_threshold=0.9
        )
        if final_ranking:
            st.session_state.final_ranking = final_ranking
    
    # Display final results
    if st.session_state.final_ranking:
        st.write("\n🎉 **Final Ranking:** 🎉")
        for i, song in enumerate(st.session_state.final_ranking, start=1):
            st.write(f"{i}. {song} (Score: {st.session_state.scores[song]:.2f}, Uncertainty: {st.session_state.uncertainties[song]:.2f})")

if __name__ == "__main__":
    main()
