/**
* Post editor - Quill WYSIWYG + auto slug + form submission
*/

document.addEventListener('DOMContentLoaded', function() {
    // Custom blots and icons (must be registered before Quill instantiation)
    // Caption toolbar icon: image frame with two text lines below it
    const Icons = Quill.import('ui/icons');
    Icons['caption'] = `<svg viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
      <rect x="1" y="1" width="16" height="9" rx="1" fill="none" stroke="currentColor" stroke-width="1.5"/>
      <line x1="2" y1="13" x2="16" y2="13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="4" y1="16" x2="14" y2="16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`;

    // Caption blot: <p class="ql-caption"> -- smaller, centred, italic
    // Used for image captions. Toggle via the caption toolbar
    const Block = Quill.import('blots/block');
    class CaptionBlot extends Block {}
    CaptionBlot.blotName = 'caption';
    CaptionBlot.tagName = 'p';
    CaptionBlot.className = 'ql-caption';
    Quill.register(CaptionBlot);

    // Quill init
    const quill = new Quill('#quill-editor', {
        theme: 'snow',
        modules: {
            toolbar: [
                [{ header: [1,2,3,false] }],
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ list: 'ordered'}, { list: 'bullet'}],
                ['link', 'image', 'video'],
                ['caption'],
                ['clean'],
            ],
        },
        placeholder: 'Write your post...'
    });

    // Image upload handler
    const imageHandler = function() {
        // capture selection before the file picker steals editor focus
        const range = quill.getSelection() || { index: quill.getLength() - 1 };

        const input = document.createElement('input');
        input.setAttribute('type', 'file');
        input.setAttribute('accept', 'image/*');
        input.addEventListener('change', function() {
            const file = input.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            // get CSRF token from meta tag
            const csrfToken = document.querySelector('meta[name="csrf-token"]');
            const headers = {};
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken.getAttribute('content');
            }

            fetch('/admin/media/upload-ajax', {
                method: "POST",
                headers: headers,
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success){
                    quill.insertEmbed(range.index, 'image', data.url);
                    quill.setSelection(range.index + 1);
                } else {
                    alert('Upload failed: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Upload error:' , error);
                alert('Upload error: ' + error.message);
            });
        });
        input.click();
    };

    quill.getModule('toolbar').addHandler('image', imageHandler);

    // Video URL conversion (Youtube/Vimeo watch URL to embed URL)
    function toEmbedUrl(url) {
        url = url.trim();
        // youtube
        let m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-z0-9_-]{11})/);
        if (m) return 'https://www.youtube.com/embed/' + m[1];
        // vimeo
        m = url.match(/vimeo\.com\/(\d+)/);
        if (m) return 'https://player.vimeo.com/video/' + m[1];
        return url;
    }

    // Caption handler
    quill.getModule('toolbar').addHandler('caption', function() {
        const format = quill.getFormat();
        quill.format('caption', !format.caption);
    });

    // Video handler
    quill.getModule('toolbar').addHandler('video', function() {
        // capture selection before prompt() steals editor focus
        const range = quill.getSelection() || { index: quill.getLength() -1 };
        const url = prompt('Enter YouTube or Vimeo URL: ');
        if (url) {
            quill.focus();
            quill.insertEmbed(range.index, 'video', toEmbedUrl(url));
            quill.setSelection(range.index + 1);
        }
    });

    // Clipboard matcher: restore caption format when loading existing posts
    // dangerouslyPasteHTML converts HTML to Delta via the clipboard module which
    // doesn't automatically map custom blot classes back to block attributes.
    // This matcher recognises <p class="ql-caption"> and applies the caption
    // attribute to the paragraph-terminating \n - where Quill stores block-level
    // formats in the Delta model. Must be registered before dangerouslyPasteHTML
    const Delta = Quill.import('delta');
    quill.clipboard.addMatcher('p.ql-caption', function(node, delta) {
        const len = delta.length();
        return delta.compose(
            new Delta().retain(len - 1).retain(1, { caption: true })
        );
    });

    // Prepopulate when editing existing post
    const bodyField = document.getElementById('post-body');
    if (bodyField && bodyField.value.trim()) {
        try {
            const delta = JSON.parse(bodyField.value);
            quill.setContents(delta, 'silent');
        } catch (e) {
            // body is nh3-sanitized html from editor, render it as formatted content
            quill.clipboard.dangerouslyPasteHTML(bodyField.value);
        }
    }

    // Copy Quill HTML into the hidden textarea before and form submission.
    // use root.innerHtml rrather than getSemanticHtml because Quill v2's
    // getSemanticHtml() serializes BlockEmbed blots (video/iframe) as anchor
    // links, losing the actual embed. root.innerHTML preserves the iframe
    function syncBody() {
        bodyField.value = quill.root.innerHTML;
    }
    window.syncBody = syncBody;

    // auto slug
    const titleInput = document.getElementById('post-title');
    const slugInput = document.getElementById('post-slug');

    if (titleInput && slugInput) {
        titleInput.addEventListener('blur', function() {
            slugInput.value = titleInput.value
                .toLowerCase()
                .replace(/\s+/g, '-')
                .replace(/[^\w-]/g, '');
        });
    }

    // Save Draft
    const saveDraftButton = document.getElementById('save-draft-btn');
    const statusField = document.getElementById('form-status');

    if (saveDraftButton) {
        saveDraftButton.addEventListener('click', function() {
            syncBody();
            statusField.value = 'draft';
            saveDraftButton.closest('form').submit();
        });
    }

    // Publish
    const publishButton = document.getElementById('publish-btn');

    if (publishButton) {
        publishButton.addEventListener('click', function() {
            syncBody();
            statusField.value = 'published';
        });
    }
});