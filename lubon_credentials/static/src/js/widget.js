openerp.lubon_credentials = function(openerp) {

    openerp.web.form.widgets.add('credentials', 'openerp.lubon_credentials.Credentials');
    openerp.lubon_credentials.Credentials = openerp.web.form.FieldChar.extend({
        template: "credentials",
        events: {
            'click .reveal_password_button': 'reveal_password',
            'click .reveal_password_content_copy': 'copy_to_clipboard',
        },
        start: function() {
            this.credentials_id = this.get('value');
            this.reveal_password();
            return this._super();
        },
        reveal_password: function() {
            var self = this;
            var model = new openerp.web.Model('lubon_credentials.credentials');

            var content_element = self.$el.find('.reveal_password_content');
            var pin_element = self.$el.find('.reveal_password_pin');
            var pin_input = pin_element.find('input[type="password"]');
            var button_element = self.$el.find('.reveal_password_button');

            model.call('reveal_credentials', [self.credentials_id, pin_input.val()]).then(function(data) {
                content_element.find('.reveal_password_content_value').text(data[0][0]).show();
                content_element.find('.reveal_password_content_copy').show();
                content_element.show();
                button_element.hide();
                pin_element.hide();
                setTimeout(function() {
                    content_element.find('.reveal_password_content_value').text('********');
                    content_element.find('.reveal_password_content_copy').hide();
                    pin_input.val('');
                    button_element.show();
                }, parseInt(data[0][1]));
            }).fail(function(result, e) {
                // e.preventDefault();
                content_element.hide();
                button_element.show();
                pin_element.show();
            });
        },
        copy_to_clipboard: function(e) {
            e.preventDefault();
            copy_to_clipboard($(e.target).prev('.reveal_password_content_value'))
        }
    });

    openerp.web.form.widgets.add('clipboard', 'openerp.lubon_credentials.Clipboard');
    openerp.lubon_credentials.Clipboard = openerp.web.form.FieldChar.extend({
        template: "FieldCharClipboard",
        events: {
            'click .content_copy': 'copy_to_clipboard',
        },
        init: function (field_manager, node) {
            this.clipboard = true;
            return this._super(field_manager, node);
        },
        start: function() {
            return this._super();
        },
        copy_to_clipboard: function(e) {
            e.preventDefault();
            copy_to_clipboard($(e.target).prev('.oe_form_char_content'))
        }
    });

    function copy_to_clipboard(element) {
        var $temp = $("<input>")
        $("body").append($temp);
        $temp.val($(element).text()).select();
        document.execCommand("copy");
        $temp.remove();
    }
}