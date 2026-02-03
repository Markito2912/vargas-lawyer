// Smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offset = 80; // navbar height
            const targetPosition = target.offsetTop - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Navbar scroll effect
const navbar = document.getElementById('navbar');
let lastScroll = 0;

if (navbar) {
    window.addEventListener('scroll', () => {
        try {
            const currentScroll = window.pageYOffset;

            if (currentScroll > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        } catch (error) {
            // Silently handle scroll error
        }
    });
}

// Mobile menu toggle
const mobileToggle = document.getElementById('mobileToggle');
const navMenu = document.getElementById('navMenu');

if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
        try {
            navMenu.classList.toggle('active');
            mobileToggle.classList.toggle('active');
        } catch (e) {
            console.error('Menu toggle error', e);
        }
    });
}

// Close mobile menu when clicking a link
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        if (navMenu && mobileToggle) {
            navMenu.classList.remove('active');
            mobileToggle.classList.remove('active');
        }
    });
});

// FAQ Accordion
const faqItems = document.querySelectorAll('.faq-item');

faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');

    question.addEventListener('click', () => {
        // Close all other items
        faqItems.forEach(otherItem => {
            if (otherItem !== item) {
                otherItem.classList.remove('active');
            }
        });

        // Toggle current item
        item.classList.toggle('active');
    });
});

// Form submission
const contactForm = document.getElementById('contactForm');

if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();

        try {
            // Get form data
            const formData = new FormData(contactForm);
            const data = Object.fromEntries(formData);

            // Here you would typically send the data to a server
            // console.log('Form submitted:', data);

            // Show success message
            alert('¡Gracias por contactarnos! Nos pondremos en contacto con usted dentro de 24 horas.');

            // Reset form
            contactForm.reset();

            // In a real application, you would send this to your backend:
            /*
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                alert('¡Gracias por contactarnos!');
                contactForm.reset();
            })
            .catch((error) => {
                alert('Hubo un error al enviar el formulario. Por favor intente nuevamente.');
            });
            */
        } catch (error) {
            alert('Error al procesar el formulario.');
        }
    });
}

// Animate on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all animated elements
document.querySelectorAll('[data-aos]').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.8s ease';
    observer.observe(el);
});

// Counter animation for stats
const animateCounter = (element, target, duration = 2000) => {
    let start = 0;
    const increment = target / (duration / 16);
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = target.toString().includes('%') ? target : target + '+';
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(start).toString();
        }
    }, 16);
};

// Observe stats
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumber = entry.target;
            const text = statNumber.textContent;
            // Only animate if the text contains numbers
            const number = parseInt(text.replace(/\D/g, ''));
            if (!isNaN(number) && number > 0) {
                animateCounter(statNumber, number);
            }
            statsObserver.unobserve(statNumber);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-number').forEach(stat => {
    statsObserver.observe(stat);
});

// Parallax effect for hero
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const heroBackground = document.querySelector('.hero-background');
    if (heroBackground) {
        heroBackground.style.transform = `translateY(${scrolled * 0.5}px)`;
    }
});

// Loading animation
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
});

// Add smooth reveal for images
const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            // Set opacity directly when revealed
            entry.target.style.opacity = '1';
            imageObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.hero-img, .team-img').forEach(img => {
    img.style.opacity = '0';
    img.style.transition = 'opacity 1s ease';
    imageObserver.observe(img);
});

// Service card tilt effect (optional enhancement)
document.querySelectorAll('.service-card, .team-card, .testimonial-card').forEach(card => {
    card.addEventListener('mouseenter', function (e) {
        this.style.transition = 'transform 0.1s ease';
    });

    card.addEventListener('mousemove', function (e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;

        this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
    });

    card.addEventListener('mouseleave', function () {
        this.style.transition = 'transform 0.3s ease';
        this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
    });
});

// Global image error handler
document.addEventListener('error', function (e) {
    if (e.target.tagName === 'IMG') {
        e.target.style.display = 'none'; // Hide broken images
        // Alternatively set a placeholder:
        // e.target.src = 'path/to/placeholder.jpg';
        console.warn('Image failed to load:', e.target.src);
    }
}, true);

// Exit Intent Modal Logic
document.addEventListener('DOMContentLoaded', () => {
    // Only run if modal exists in the page
    const exitModal = document.getElementById('exitModal');
    if (!exitModal) return;

    const closeModal = document.querySelector('.close-modal');
    let modalShown = false;

    function showExitModal() {
        // Check if user already closed it in this session
        if (!sessionStorage.getItem('exitModalClosed')) {
            exitModal.style.display = 'block';
            modalShown = true;
        }
    }

    // Show modal on mouse leave (Desktop)
    document.addEventListener('mouseleave', function(e) {
        if (e.clientY < 0 && !modalShown) {
            showExitModal();
        }
    });

    // Show modal after 30s on mobile (if not shown)
    setTimeout(() => {
        if (!modalShown) {
            showExitModal();
        }
    }, 30000);

    // Close modal actions
    if (closeModal) {
        closeModal.onclick = function() {
            exitModal.style.display = 'none';
            sessionStorage.setItem('exitModalClosed', 'true');
        }
    }

    window.onclick = function(event) {
        if (event.target == exitModal) {
            exitModal.style.display = 'none';
            sessionStorage.setItem('exitModalClosed', 'true');
        }
    }
});

// LexElite website loaded
