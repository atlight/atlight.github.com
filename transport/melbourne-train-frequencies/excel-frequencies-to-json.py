import openpyxl
from openpyxl.cell.cell import MergedCell
import json

filename = r"C:\Users\athomas3\Personal\OneDrive\Rail\Frequencies.xlsx"
# filename = r"C:\Users\Alan Thomas\OneDrive\Rail\Frequencies.xlsx"

# Load the workbook
wb = openpyxl.load_workbook(filename)

# Dictionary that is written as JSON
data = dict()

# Go through relevant sheets
for year in ['1939', '1974', '1990', '2005', '2014', '2023', '2026']:
  sheet = wb[year]

  data[year] = dict()

  # Collect frequency data for each row
  for (index, row) in enumerate(sheet.iter_rows()):
    # skip first 4 rows
    if index < 4:
      continue
    
    # Identify name of line/section
    if row[7].value:
      lineName = row[7].value
      data[year][lineName] = dict()
    elif isinstance(row[7], MergedCell):
      for mergedCell in sheet.merged_cells.ranges:
        if row[7].coordinate in mergedCell:
            lineName = mergedCell.start_cell.value
            data[year][lineName] = dict()
    else:
      # this row is blank; set it as a spacer
      lineName = f'spacer-{index}'
      rowHeight = sheet.row_dimensions[index + 1].height
      if rowHeight and rowHeight < 6:
        data[year][lineName] = {
          "spacerType": 1
        }
      else:
        data[year][lineName] = {
          "spacerType": 2
        }

    # Store line color
    if (
      row[0].fill and row[0].fill.fgColor and row[0].fill.fgColor.type == 'rgb' and
      not row[0].fill.fgColor.rgb.startswith('00')
    ):
      data[year][lineName]['color'] = '#' + row[0].fill.fgColor.rgb[2:]
    else:
      data[year][lineName]['color'] = None

    # If a spacer, we are done
    if 'spacer-' in lineName:
      continue

    # Collect frequency data
    for (section, cells) in {
      "weekday": row[9:94],
      "saturday": row[96:188] if (not year.isdigit() or int(year) >= 2014) else row[96:179],
      "sunday": row[188:271] if (not year.isdigit() or int(year) >= 2014) else row[183:268]
    }.items():
      sectionNote = None
      tds = []
      
      
      for cell in cells:
        if isinstance(cell, MergedCell):
          if len(tds) == 0:
            tds.append({
              "fillClass": [],
              "otherClass": [],
              "content": '',
              "colspan": 1
            })

          tds[-1]['colspan'] += 1
        else:
          # not a merged cell. Decide whether we should merge
          # this into the previous cell or start a new cell
          td = {
            "fillClass": [],
            "otherClass": [],
            "content": '',
            "colspan": 1
          }

          # store cell fill
          if not cell.fill:
            td['fillClass'].append('c')
            td['fillClass'].append('c0')
          elif cell.fill.fgColor.type == 'theme' and \
            (cell.fill.fgColor.theme != 0 or cell.fill.fgColor.tint != 0):
            td['fillClass'].append('c')
            td['fillClass'].append(f'c{cell.fill.fgColor.index}')
          
          # store cell border
          if cell.border.left.style == 'thin' and not cell.comment:
            td['otherClass'].append('bl')
          if cell.border.right.style == 'thin':
            td['otherClass'].append('br')

          # store section note if any
          if cell.comment:
            if sectionNote:
              raise Exception(f'duplicate note found on {year}/{lineName}/{section}')
            if 'Alan' in cell.comment.text:
              raise Exception(f'name left in a note on {year}/{lineName}/{section}')
            sectionNote = cell.comment.text

          # store cell content if present, otherwise add a 'd' (default text) class
          if cell.value:
            td['content'] = str(cell.value)
          else:
            td['content'] = ''
            td['otherClass'].append('d')

          # merge into the previous cell if:
          #   - a previous cell ex
          #   - either cell has no content
          #   - the cell's fill classes are the same
          #   - the current cell lacks a left border
          #   - the previous cell lacks a right border
          if (
            len(tds) > 0 and
            (tds[-1]['content'] == '' or td['content'] == '') and
            tds[-1]['fillClass'] == td['fillClass'] and
            'bl' not in td['otherClass'] and
            'br' not in tds[-1]['otherClass']
          ):
            tds[-1]['colspan'] += 1
            tds[-1]['content'] += td['content']
            if 'br' in td['otherClass']:
              tds[-1]['otherClass'].append('br')
          else:
            # not a merged cell. Add cell to the row and continue
            tds.append(td)
      
      # Store these tds to list
      data[year][lineName][section] = ''
      for td in tds:
        # work out if we should put a default caption
        if (
          (not td['content'] and td['colspan'] >= 5) or 
          (len(td['content']) == 1 and td['colspan'] >= 7) 
        ):
          origContent = td['content']
          if 'c4' in td['fillClass']: td['content'] = '<d>40</d>'
          if 'c5' in td['fillClass']: td['content'] = '<d>30</d>'
          if 'c6' in td['fillClass']: td['content'] = '<d>20</d>'
          if 'c7' in td['fillClass']: td['content'] = '<d>15</d>'
          if 'c8' in td['fillClass']: td['content'] = '<d>10</d>'
          if 'c9' in td['fillClass']: td['content'] = '<d>5</d>'
          if 'c0' in td['fillClass']: td['content'] = '<d>60</d>'
          if origContent:
            td['content'] += ' <b>' + origContent + '</b>'
        elif len(td['content']) == 1:
            td['content'] = '<b>' + td['content'] + '</b>'

        data[year][lineName][section] += '<td'
        if td['colspan'] > 1:
          data[year][lineName][section] += f' colspan="{td['colspan']}"'
        if len(td['fillClass']) > 0 or len(td['otherClass']) > 0:
          data[year][lineName][section] += f' class="{' '.join(td['fillClass'] + td['otherClass']).rstrip()}"'
        data[year][lineName][section] += '>'
        if td['content']:
          data[year][lineName][section] += f'<span>{td['content']}</span>'
        data[year][lineName][section] += '</td>'

      if sectionNote:
        data[year][lineName][f'{section}-note'] = sectionNote

# Print out the results
with open('data.json', 'w') as file:
  json.dump(data, file)
