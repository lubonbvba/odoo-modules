openerp.lubon_credentials = function(openerp) {

    openerp.web.form.widgets.add('credentials', 'openerp.lubon_credentials.Credentials');
    openerp.lubon_credentials.Credentials = openerp.web.form.FieldChar.extend({
        template: "credentials",
        events: {
            'click .reveal_password_button': 'reveal_password',
        },
        start: function() {
            var self = this;

            this.credentials_id = this.get('value');
            this.reveal_password();

            return this._super();
        },
        render_value: function() {
            if (!this.get("effective_readonly")) {
                this.$el.find('input').val('');
            }
        },
        reveal_password: function() {
            var self = this;

            var model = new openerp.web.Model('lubon_credentials.credentials');

            var content_element = self.$el.find('.reveal_password_content');
            var pin_element = self.$el.find('.reveal_password_pin');
            var pin_input = pin_element.find('input[type="password"]');
            var button_element = self.$el.find('.reveal_password_button');

            model.call('reveal_credentials', [self.credentials_id, pin_input.val()]).then(function(data) {
                if (data[0] === -1) {
                    openerp.web.redirect('/web/login');
                }
                content_element.find('.reveal_password_content_value').text(data[0][0]).show();
                content_element.find('.reveal_password_content_copy').show();
                content_element.show();
                button_element.hide();
                pin_element.hide();
                var copy_sel = content_element.find('.reveal_password_content_copy');
                copy_sel.on('click', function(e) {
                    e.preventDefault();
                });
                copy_sel.clipboard({
                    path: '/lubon_credentials/static/src/swf/jquery.clipboard.swf',
                    copy: function() {
                        var value = copy_sel.parents('.reveal_password_content:first').find('.reveal_password_content_value').text();
                        return value;
                    }
                });
                setTimeout(function() {
                    content_element.find('.reveal_password_content_value').text('********');
                    content_element.find('.reveal_password_content_copy').hide();
                    pin_input.val('');
                    button_element.show();
                }, parseInt(data[0][1]));
            }).fail(function(result, e) {
                e.preventDefault();
                var error = result.data.message.split(/\n/);
                openerp.webclient.notification.warn(error[0],error[1]);
                content_element.hide();
                button_element.show();
                pin_element.show();
            });
        }
    });

    openerp.web.form.widgets.add('clipboard', 'openerp.lubon_credentials.Clipboard');
    openerp.lubon_credentials.Clipboard = openerp.web.form.FieldChar.extend({
        template: "FieldCharClipboard",
        init: function(field_manager, node) {
            this.clipboard = true;
            return this._super(field_manager, node);
        },
        start: function() {
            var self = this;

            var copy_sel = self.$el.find('.content_copy');
            copy_sel.on('click', function(e) {
                e.preventDefault();
            });
            copy_sel.clipboard({
                path: '/lubon_credentials/static/src/swf/jquery.clipboard.swf',
                copy: function() {
                    var value = copy_sel.prev('.oe_form_char_content').text();
                    return value;
                }
            });

            return this._super();
        }
    });


    openerp.web.form.widgets.add('password', 'openerp.lubon_credentials.Password');
    openerp.lubon_credentials.Password = openerp.web.form.FieldChar.extend({
        template: "lubon_password",
        events: {
            'click .reveal_password_button': 'reveal_password',
        },
        start: function() {
            var self = this;

            return this._super();
        },
        render_value: function() {
            if (!this.get("effective_readonly")) {
                this.$el.find('input').val('');
            }
        },
        reveal_password: function() {
            var self = this;

            var model = new openerp.web.Model(self.view.dataset.model);

            var content_element = self.$el.find('.reveal_password_content');
            var pin_element = self.$el.find('.reveal_password_pin');
            var pin_input = pin_element.find('input[type="password"]');
            var button_element = self.$el.find('.reveal_password_button');

            model.call('reveal_credentials', [self.view.datarecord.id, pin_input.val()]).then(function(data) {
                if (data[0] === -1) {
                    openerp.web.redirect('/web/login');
                }
                content_element.find('.reveal_password_content_value').text(data[0][0]).show();
                content_element.find('.reveal_password_content_copy').show();
                content_element.show();
                button_element.hide();
                pin_element.hide();
                var copy_sel = content_element.find('.reveal_password_content_copy');
                copy_sel.on('click', function(e) {
                    e.preventDefault();
                });
                copy_sel.clipboard({
                    path: '/lubon_credentials/static/src/swf/jquery.clipboard.swf',
                    copy: function() {
                        var value = copy_sel.parents('.reveal_password_content:first').find('.reveal_password_content_value').text();
                        return value;
                    }
                });
                setTimeout(function() {
                    content_element.find('.reveal_password_content_value').text('********');
                    content_element.find('.reveal_password_content_copy').hide();
                    pin_input.val('');
                    button_element.show();
                }, parseInt(data[0][1]));
            }).fail(function(result, e) {
                e.preventDefault();
                var error = result.data.message.split(/\n/);
                openerp.webclient.notification.warn(error[0],error[1]);
                content_element.hide();
                button_element.show();
                pin_element.show();
            });
        }
    });
}