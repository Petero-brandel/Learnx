import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Course, Module, Lesson

courses_data = [
    {
        'slug': 'prompt-engineering',
        'title': 'Mastering Prompt Engineering',
        'description': 'Learn to craft prompts that get exactly the output you need from any AI model.',
        'price': 25000.00,
        'thumbnail': '/images/courses/course-1.jpg',
    },
    {
        'slug': 'ai-content',
        'title': 'AI Content Creation Masterclass',
        'description': 'Generate blog posts, ad copy, social media content, and visuals using AI tools.',
        'price': 20000.00,
        'thumbnail': '/images/courses/course-2.jpg',
    },
    {
        'slug': 'digital-marketing',
        'title': 'Digital Marketing Mastery',
        'description': 'From SEO to paid ads — master the strategies that drive real business results.',
        'price': 30000.00,
        'thumbnail': '/images/courses/course-3.jpg',
    },
    {
        'slug': 'ai-bootcamp',
        'title': 'AI Business Bootcamp',
        'description': 'Transform your business operations and scale faster using AI automation and tools.',
        'price': 50000.00,
        'thumbnail': '/images/courses/course-1.jpg',
    },
    {
        'slug': 'social-media-growth',
        'title': 'Social Media Growth Hacks',
        'description': 'Master algorithms and organic growth strategies across TikTok, Instagram, and LinkedIn.',
        'price': 15000.00,
        'thumbnail': '/images/courses/course-2.jpg',
    },
    {
        'slug': 'chatgpt-mastery',
        'title': 'ChatGPT Complete Mastery',
        'description': 'From basics to advanced applications — become a ChatGPT power user in one weekend.',
        'price': 10000.00,
        'thumbnail': '/images/courses/course-3.jpg',
    }
]

def seed():
    print("Seeding courses...")
    for data in courses_data:
        course, created = Course.objects.get_or_create(
            slug=data['slug'],
            defaults={
                'title': data['title'],
                'description': data['description'],
                'price': data['price'],
                'thumbnail': data['thumbnail'],
                'is_published': True
            }
        )
        if created:
            # Create some dummy modules and lessons
            mod = Module.objects.create(course=course, title='Module 1: Introduction', order=0)
            Lesson.objects.create(module=mod, title='Lesson 1: Welcome', content_type='video', order=0, is_preview=True)
            Lesson.objects.create(module=mod, title='Lesson 2: Getting Started', content_type='video', order=1, is_preview=False)
            
            print(f"Created course: {course.title}")
        else:
            print(f"Course already exists: {course.title}")
            
    print("Done seeding courses.")

if __name__ == '__main__':
    seed()
