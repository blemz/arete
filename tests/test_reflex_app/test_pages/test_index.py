"""Tests for index page."""
import pytest
from unittest.mock import Mock, patch
import reflex as rx
from src.arete.ui.reflex_app.pages.index import IndexPage


class TestIndexPage:
    """Test cases for IndexPage."""

    @pytest.fixture
    def index_page(self):
        """IndexPage instance for testing."""
        return IndexPage()

    def test_index_page_initialization(self, index_page):
        """Test index page initialization."""
        assert index_page is not None
        assert hasattr(index_page, 'render')

    def test_render_landing_page(self, index_page):
        """Test rendering landing page."""
        rendered = index_page.render()
        
        assert rendered is not None

    def test_hero_section_component(self, index_page):
        """Test hero section component."""
        hero = index_page.create_hero_section()
        
        assert hero is not None

    def test_features_overview_component(self, index_page):
        """Test features overview component."""
        features = [
            {
                "title": "AI-Powered Philosophy Tutor",
                "description": "Get personalized guidance through classical philosophical texts",
                "icon": "brain"
            },
            {
                "title": "Interactive Knowledge Graph",
                "description": "Explore connections between philosophical concepts and thinkers",
                "icon": "network"
            },
            {
                "title": "Citation-Backed Responses",
                "description": "Every answer includes accurate references to original texts",
                "icon": "quote"
            }
        ]
        
        features_section = index_page.create_features_section(features)
        
        assert features_section is not None

    def test_navigation_menu(self, index_page):
        """Test navigation menu component."""
        nav_menu = index_page.create_navigation_menu()
        
        assert nav_menu is not None

    def test_quick_start_guide(self, index_page):
        """Test quick start guide component."""
        quick_start = index_page.create_quick_start_guide()
        
        assert quick_start is not None

    def test_demo_section(self, index_page):
        """Test demo section component."""
        demo_section = index_page.create_demo_section()
        
        assert demo_section is not None

    def test_testimonials_section(self, index_page):
        """Test testimonials section."""
        testimonials = [
            {
                "text": "Arete has transformed how I study philosophy. The AI tutor is incredibly knowledgeable.",
                "author": "Sarah Chen",
                "role": "Philosophy Graduate Student"
            },
            {
                "text": "The citation system is amazing. I can trace every concept back to its source.",
                "author": "Dr. Michael Thompson",
                "role": "Professor of Philosophy"
            }
        ]
        
        testimonials_section = index_page.create_testimonials_section(testimonials)
        
        assert testimonials_section is not None

    def test_statistics_showcase(self, index_page):
        """Test statistics showcase component."""
        stats = {
            "total_texts": 150,
            "concepts_mapped": 2500,
            "active_users": 1200,
            "citations_available": 15000
        }
        
        stats_section = index_page.create_statistics_section(stats)
        
        assert stats_section is not None

    def test_call_to_action_buttons(self, index_page):
        """Test call-to-action buttons."""
        cta_primary = index_page.create_primary_cta("Start Learning")
        cta_secondary = index_page.create_secondary_cta("View Demo")
        
        assert cta_primary is not None
        assert cta_secondary is not None

    def test_footer_component(self, index_page):
        """Test footer component."""
        footer = index_page.create_footer()
        
        assert footer is not None

    def test_responsive_design_mobile(self, index_page):
        """Test responsive design for mobile."""
        with patch.object(index_page, 'is_mobile_view', return_value=True):
            mobile_layout = index_page.render_mobile_layout()
            
            assert mobile_layout is not None

    def test_responsive_design_tablet(self, index_page):
        """Test responsive design for tablet."""
        with patch.object(index_page, 'is_tablet_view', return_value=True):
            tablet_layout = index_page.render_tablet_layout()
            
            assert tablet_layout is not None

    def test_responsive_design_desktop(self, index_page):
        """Test responsive design for desktop."""
        with patch.object(index_page, 'is_desktop_view', return_value=True):
            desktop_layout = index_page.render_desktop_layout()
            
            assert desktop_layout is not None

    def test_theme_support(self, index_page):
        """Test theme support."""
        with patch.object(index_page, 'apply_theme') as mock_theme:
            index_page.set_theme("dark")
            
            mock_theme.assert_called_once_with("dark")

    def test_accessibility_features(self, index_page):
        """Test accessibility features."""
        with patch.object(index_page, 'add_accessibility_attributes') as mock_a11y:
            index_page.ensure_accessibility()
            
            mock_a11y.assert_called_once()

    def test_loading_states(self, index_page):
        """Test loading states."""
        loading_component = index_page.create_loading_state()
        
        assert loading_component is not None

    def test_error_handling(self, index_page):
        """Test error handling."""
        error_component = index_page.create_error_state("Failed to load")
        
        assert error_component is not None

    def test_meta_tags_generation(self, index_page):
        """Test meta tags generation for SEO."""
        meta_tags = index_page.generate_meta_tags()
        
        assert "title" in meta_tags
        assert "description" in meta_tags
        assert "keywords" in meta_tags

    def test_structured_data_markup(self, index_page):
        """Test structured data markup."""
        structured_data = index_page.generate_structured_data()
        
        assert "@type" in structured_data
        assert "name" in structured_data
        assert "description" in structured_data

    def test_performance_metrics(self, index_page):
        """Test performance metrics tracking."""
        with patch.object(index_page, 'track_page_load_time') as mock_track:
            index_page.track_performance_metrics()
            
            mock_track.assert_called_once()

    def test_analytics_integration(self, index_page):
        """Test analytics integration."""
        with patch.object(index_page, 'send_analytics_event') as mock_analytics:
            index_page.track_user_interaction("hero_cta_click")
            
            mock_analytics.assert_called_once()

    def test_interactive_elements(self, index_page):
        """Test interactive elements."""
        # Test hover effects
        with patch.object(index_page, 'add_hover_effects') as mock_hover:
            index_page.setup_interactive_elements()
            
            mock_hover.assert_called_once()

    def test_scroll_animations(self, index_page):
        """Test scroll animations."""
        with patch.object(index_page, 'setup_scroll_animations') as mock_animations:
            index_page.enable_scroll_animations()
            
            mock_animations.assert_called_once()

    def test_page_transitions(self, index_page):
        """Test page transitions."""
        with patch.object(index_page, 'setup_page_transitions') as mock_transitions:
            index_page.enable_page_transitions()
            
            mock_transitions.assert_called_once()

    def test_social_media_integration(self, index_page):
        """Test social media integration."""
        social_links = index_page.create_social_media_links()
        
        assert social_links is not None

    def test_newsletter_signup(self, index_page):
        """Test newsletter signup component."""
        newsletter = index_page.create_newsletter_signup()
        
        assert newsletter is not None

    def test_contact_information(self, index_page):
        """Test contact information display."""
        contact_info = index_page.create_contact_info()
        
        assert contact_info is not None

    def test_language_selector(self, index_page):
        """Test language selector component."""
        languages = ["en", "es", "fr", "de", "it", "zh", "ja"]
        
        language_selector = index_page.create_language_selector(languages)
        
        assert language_selector is not None

    def test_search_functionality(self, index_page):
        """Test search functionality on landing page."""
        search_component = index_page.create_search_component()
        
        assert search_component is not None

    def test_breadcrumb_navigation(self, index_page):
        """Test breadcrumb navigation."""
        breadcrumbs = [
            {"label": "Home", "url": "/", "active": True}
        ]
        
        breadcrumb_nav = index_page.create_breadcrumbs(breadcrumbs)
        
        assert breadcrumb_nav is not None

    def test_featured_content_carousel(self, index_page):
        """Test featured content carousel."""
        featured_items = [
            {"title": "Introduction to Virtue Ethics", "image": "virtue.jpg", "link": "/virtue"},
            {"title": "Plato's Theory of Forms", "image": "forms.jpg", "link": "/forms"},
            {"title": "Aristotelian Logic", "image": "logic.jpg", "link": "/logic"}
        ]
        
        carousel = index_page.create_featured_carousel(featured_items)
        
        assert carousel is not None

    def test_video_background_component(self, index_page):
        """Test video background component."""
        video_bg = index_page.create_video_background("intro_video.mp4")
        
        assert video_bg is not None

    def test_parallax_scrolling(self, index_page):
        """Test parallax scrolling effects."""
        with patch.object(index_page, 'setup_parallax_effects') as mock_parallax:
            index_page.enable_parallax_scrolling()
            
            mock_parallax.assert_called_once()

    def test_progressive_web_app_features(self, index_page):
        """Test PWA features."""
        pwa_config = index_page.generate_pwa_manifest()
        
        assert "name" in pwa_config
        assert "short_name" in pwa_config
        assert "theme_color" in pwa_config

    def test_cookie_consent_banner(self, index_page):
        """Test cookie consent banner."""
        consent_banner = index_page.create_cookie_consent_banner()
        
        assert consent_banner is not None

    def test_site_announcement_banner(self, index_page):
        """Test site announcement banner."""
        announcement = {
            "message": "New feature: Advanced Analytics Dashboard now available!",
            "type": "info",
            "dismissible": True
        }
        
        banner = index_page.create_announcement_banner(announcement)
        
        assert banner is not None

    def test_user_onboarding_flow(self, index_page):
        """Test user onboarding flow."""
        onboarding_steps = [
            {"title": "Welcome", "content": "Welcome to Arete!"},
            {"title": "Features", "content": "Explore our key features"},
            {"title": "Get Started", "content": "Ready to begin learning?"}
        ]
        
        onboarding = index_page.create_onboarding_flow(onboarding_steps)
        
        assert onboarding is not None

    def test_feedback_collection(self, index_page):
        """Test feedback collection component."""
        feedback_form = index_page.create_feedback_form()
        
        assert feedback_form is not None

    def test_help_and_support_links(self, index_page):
        """Test help and support links."""
        support_links = index_page.create_support_links()
        
        assert support_links is not None

    def test_pricing_information(self, index_page):
        """Test pricing information display."""
        pricing_tiers = [
            {"name": "Free", "price": 0, "features": ["Basic access", "Limited queries"]},
            {"name": "Pro", "price": 9.99, "features": ["Unlimited queries", "Advanced analytics"]},
            {"name": "Academic", "price": 4.99, "features": ["Student discount", "Export features"]}
        ]
        
        pricing_section = index_page.create_pricing_section(pricing_tiers)
        
        assert pricing_section is not None

    def test_faq_section(self, index_page):
        """Test FAQ section."""
        faqs = [
            {"question": "What is Arete?", "answer": "Arete is an AI-powered philosophy tutor..."},
            {"question": "How accurate are the citations?", "answer": "All citations are verified against original texts..."},
            {"question": "Can I export my conversations?", "answer": "Yes, you can export in multiple formats..."}
        ]
        
        faq_section = index_page.create_faq_section(faqs)
        
        assert faq_section is not None

    def test_blog_preview_section(self, index_page):
        """Test blog preview section."""
        blog_posts = [
            {"title": "Understanding Virtue Ethics", "excerpt": "Explore the foundations...", "date": "2025-01-01"},
            {"title": "Plato vs Aristotle", "excerpt": "Compare their philosophies...", "date": "2025-01-02"}
        ]
        
        blog_preview = index_page.create_blog_preview(blog_posts)
        
        assert blog_preview is not None

    def test_integration_showcase(self, index_page):
        """Test integration showcase."""
        integrations = [
            {"name": "Zotero", "description": "Citation management", "logo": "zotero.png"},
            {"name": "Notion", "description": "Note taking", "logo": "notion.png"},
            {"name": "Obsidian", "description": "Knowledge graphs", "logo": "obsidian.png"}
        ]
        
        integration_section = index_page.create_integration_showcase(integrations)
        
        assert integration_section is not None

    def test_security_badges(self, index_page):
        """Test security badges display."""
        security_badges = index_page.create_security_badges()
        
        assert security_badges is not None

    def test_page_loading_optimization(self, index_page):
        """Test page loading optimization."""
        with patch.object(index_page, 'optimize_images') as mock_optimize:
            with patch.object(index_page, 'lazy_load_components') as mock_lazy:
                index_page.optimize_page_loading()
                
                mock_optimize.assert_called_once()
                mock_lazy.assert_called_once()