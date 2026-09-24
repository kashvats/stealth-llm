import re

file_path = r'c:\Users\human-bot\projects\modg\master_technical_questions.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_part = """--- PART X: HTML, CSS & ACCESSIBILITY (FRONTEND FOUNDATIONS) ---

[1-10 Years: UI Fundamentals]
- What is the 'CSS Box Model'? Explain margin, border, padding, and content.
- Explain 'Semantic HTML'. Why is it important for SEO and Accessibility (a11y)?
- What is the difference between 'display: none' and 'visibility: hidden'?
- Explain 'Flexbox' vs 'CSS Grid'. When would you use one over the other?
- How does 'CSS Specificity' work? How is the weight of a selector calculated?
- What is the 'Stacking Context' and how does 'z-index' actually work?
- Explain 'Responsive Web Design'. What are Media Queries and the Mobile-First approach?
- What are 'Pseudo-classes' (e.g., :hover) vs 'Pseudo-elements' (e.g., ::before)?
- How do you optimize Web Accessibility? Discuss ARIA roles, contrast ratios, and keyboard navigation.
- Discuss styling architectures: Vanilla CSS vs BEM vs Utility-first (Tailwind) vs CSS-in-JS.

"""

# Insert right before JAVASCRIPT
content = content.replace("--- PART 13: JAVASCRIPT", new_part + "--- PART X: JAVASCRIPT")

# Re-index all parts
parts = re.split(r'--- PART \d+:', content)
if len(parts) > 1:
    reindexed_content = parts[0]
    for i in range(1, len(parts)):
        # some parts might have had 'X' if we replaced it, let's fix that
        part_body = parts[i]
        # Remove any leading 'X:' if it got caught in the split, but our regex specifically looks for \d+
        pass
    
# Wait, the regex split might miss 'PART X'. Let's just do a clean pass.
