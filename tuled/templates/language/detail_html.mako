<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "languages" %>
<%! multirow = True %>
<%block name="title">${_('Language')} ${ctx.name}</%block>

<div class="row-fluid">
    <div class="span8">
        <h2>${_('Language')} ${ctx.name}</h2>
        <h4>Sources</h4>
        <ul>
            % for source in ctx.sources:
                <li>${h.link(request, source, label=source.description)}<br />
                <small>${h.link(request, source)}</small></li>
            % endfor
        </ul>
    </div>
    <div class="span4">
        <div class="well-small well">
            ${request.map.render()}
            ${h.format_coordinates(ctx)}
        </div>
    </div>
</div>
<div class="row-fluid">
    <div class="span12">
        ${request.get_datatable('values', h.models.Value, language=ctx).render()}
    </div>
</div>
