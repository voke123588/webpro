// This script handles dynamic behaviors on profile and welcome pages

document.addEventListener('DOMContentLoaded', () => {
  // Fallback for missing extra images
  const photoSections = document.querySelectorAll('.extra-photos');
  photoSections.forEach(section => {
    if (section.children.length === 0) {
      section.innerHTML = '<p>No extra photos available.</p>';
    }
  });

  // Fallback for missing video elements
  const videoSections = document.querySelectorAll('.videos');
  videoSections.forEach(section => {
    if (!section.querySelector('video')) {
      section.innerHTML = '<p>No video available.</p>';
    }
  });

  // Optional: handle "show more" toggles for long descriptions (if needed)
  const moreToggles = document.querySelectorAll('.toggle-description');
  moreToggles.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.target);
      if (target.classList.contains('expanded')) {
        target.classList.remove('expanded');
        btn.textContent = 'Show More';
      } else {
        target.classList.add('expanded');
        btn.textContent = 'Show Less';
      }
    });
  });
});