import json
from typing import List

from injector import inject
from sqlalchemy import text

from ..configuration.models.application import ApplicationConfig
from ..dependency import IScoped
from ..json import JsonConvert


@JsonConvert.register
class Pagination:

    def __init__(self,
                 Filter: str = None,
                 Page: int = None,
                 PageUrl: str = None,
                 Limit: int = None,
                 TotalPage: int = None,
                 TotalCount: int = None
                 ):
        self.Filter: str = Filter
        self.Page: int = Page
        self.PageUrl: str = PageUrl
        self.Limit: int = Limit
        self.TotalPage: int = TotalPage
        self.TotalCount: int = TotalCount


class HtmlTemplateService(IScoped):
    @inject
    def __init__(self,
                 application_config: ApplicationConfig

                 ):
        self.application_config: ApplicationConfig = application_config

    @property
    def default_css(self):
        pagination_css = '''

            .pagination {
              display: table;
            margin: 0 auto;
                padding: 20px;
            }

            .pagination a {
              color: black;
              float: left;
              padding: 8px 16px;
              text-decoration: none;
              transition: background-color .3s;
              border: 1px solid #ddd;
            }

            .pagination a.active {
              background-color: #4CAF50;
              color: white;
              border: 1px solid #4CAF50;
            }

            .pagination a:hover:not(.active) {background-color: #ddd;}
'''
        return '''
            .wrapper{
                margin: 0 auto;
                padding: 20px;
            }    
            .container600 {
                width: 300px;
                max-width: 100%;
            }

            @media all and (max-width: 600px) {
                .container600 {
                    width: 100% !important;
                }
            }

            .col49 {
                width: 49%;
            }

            .col2 {
                width: 2%;
            }

            .col50 {
                width: 50%;
            }

            @media all and (max-width: 599px) {
                .fluid {
                    width: 100% !important;
                }
                .reorder {
                    width: 100% !important;
                    margin: 0 auto 10px;
                }
                .ghost-column {
                    display:none;
                    height:0;
                    width:0;
                    overflow:hidden;
                    max-height:0;
                    max-width:0;
                }
            }
            .pdi-column{
                text-align: left;
                padding:4px; 
                font-family: Arial,sans-serif; 
                font-size: 12px; 
                line-height:10px;
            }
            .pdi-row{
                text-align: left;
                padding:4px; 
                font-family: Arial,sans-serif; 
                font-size: 10px; 
                line-height:10px;
            }
            .row-nowrap{
                white-space: nowrap;
            }
            table {
              border-collapse: collapse;
              width: 100%;
            }

            th, td {
              text-align: left;
              padding: 8px;
            }

            tr:nth-child(even) {background-color: #f2f2f2;}

ul.breadcrumb {
  padding: 10px 16px;
  list-style: none;
  background-color: #eee;
}
ul.breadcrumb li {
  display: inline;
  font-size: 18px;
}
ul.breadcrumb li+li:before {
  padding: 8px;
  color: black;
  content: "/\00";
}
ul.breadcrumb li a {
  color: #0275d8;
  text-decoration: none;
}
ul.breadcrumb li a:hover {
  color: #01447e;
  text-decoration: underline;
}
            ''' + pagination_css

    def mail_html_template(self, body, mail_css=None):
        css = mail_css if mail_css is not None else self.default_css
        template = f'''
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <title></title>
                <style>{css}</style>
            </head>
            <body>

                {body}
            </body>
        </html>
        '''
        return template

    def get_nullable_dict_value(self, dict, key):
        if key in dict:
            return dict[key]
        return None

    def get_dict_value(self, dict, key):
        if key in dict and dict[key] is not None:
            return dict[key]
        return ''

    def prepare_table_data_dynamic(self, query, headers, prepare_row, sortable=None, pagination: Pagination = None):

        if sortable is not None:
            query = query.order_by(text(sortable))
        pagination_json = None
        if pagination is not None:
            total_count = query.count()
            if pagination.Limit is None or pagination.Limit < 1 or pagination.Limit > 200:
                pagination.Limit = 50
            total_page = int(total_count / pagination.Limit) + 1
            if pagination.Page is None or pagination.Page < 1 or total_page < pagination.Page:
                pagination.Page = 1
            if pagination.Limit:
                query = query.limit(pagination.Limit)
            if pagination.Page:
                offset = (pagination.Page - 1) * pagination.Limit
                if offset is None or offset <= 0:
                    offset = 0
                query = query.offset(offset)
            pagination_json = {'PageUrl': pagination.PageUrl, 'PageNumber': pagination.Page, 'Limit': pagination.Limit,
                               'Count': total_count, 'TotalPage': total_page, 'Filter': pagination.Filter}
        rows = []
        for data in query:
            row = prepare_row(data)
            rows.append(row)
        return {'columns': headers, 'rows': rows,
                'pagination': pagination_json}

    def render_table(self, source, width=None):
        columns: List[str] = self.get_nullable_dict_value(source, 'columns')
        rows: List[str] = self.get_nullable_dict_value(source, 'rows')
        pagination_json = self.get_nullable_dict_value(source, 'pagination')
        headers = ''
        headers = headers + f'<th scope="col"  class="pdi-column">#</th>'
        for column in columns:
            column_style = self.get_dict_value(column, 'style')
            column_class = self.get_dict_value(column, 'class')
            column_value = self.get_dict_value(column, 'value')
            headers = headers + f'<th scope="col" style="{column_style}" class="pdi-column {column_class}">{column_value}</th>'
        bodies = ''
        index = 0
        for row in rows:
            bodies = bodies + '<tr>'
            index = index + 1
            bodies = bodies + f'<td valign="top" class="pdi-row ">{index}</td>'
            for data in row['data']:
                row_style = self.get_dict_value(data, 'style')
                row_class = self.get_dict_value(data, 'class')
                row_value = self.get_dict_value(data, 'value')
                bodies = bodies + f'<td valign="top" style="{row_style}" class="pdi-row {row_class}">{row_value}</td>'
            bodies = bodies + '</tr>'
        table_width = width if width is not None else '100%'
        pagination_html = ''
        if pagination_json is not None:
            page_data = ""
            # JsonConvert.register(Pagination)
            pagination = JsonConvert.FromJSON(json.dumps(pagination_json))

            # TotalPage = self.get_nullable_dict_value(pagination, 'TotalPage')
            for page in range(1, pagination.TotalPage + 1):
                filter = f'{pagination.Filter}' if pagination.Filter is not None and pagination.Filter != '' else ''
                page_url = pagination.PageUrl.format(f'?PageNumber={page}&Limit={pagination.Limit}&Filter={filter}')
                if page == pagination.PageNumber:
                    page_data = f'{page_data}<a href="{page_url}" class="active">{page}</a>'

                else:
                    page_data = f'{page_data}<a href="{page_url}" >{page}</a>'

            pagination_html = f'''
            <div class="pagination">
              {page_data}
            </div>
            '''
        table = f'''
        <table width="{table_width}" cellpadding="0" cellspacing="0" style="min-width:100%;">
                <thead>
                  {headers}
                </thead>
                <tbody>
                  {bodies}
                </tbody>
            </table>
            {pagination_html}
            '''
        return table

    def render_html(self,
                    content,
                    ):

        body_content = f'''

                <div class="wrapper">
                    {content}
                </div>
                '''
        mail_body = self.mail_html_template(body_content)
        return mail_body
