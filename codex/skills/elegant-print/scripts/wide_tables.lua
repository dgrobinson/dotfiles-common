-- Reusable Pandoc table normalization and orientation for Elegant Print.

local table_number = 0

local function number_set(value)
  local result = {}
  for number in string.gmatch(value or "", "%d+") do
    result[tonumber(number)] = true
  end
  return result
end

local forced_landscape = number_set(os.getenv("ELEGANT_PRINT_LANDSCAPE_TABLES"))
local forced_portrait = number_set(os.getenv("ELEGANT_PRINT_PORTRAIT_TABLES"))
local landscape_threshold = tonumber(os.getenv("ELEGANT_PRINT_LANDSCAPE_THRESHOLD")) or 4

local function has_rows(body)
  return #body.head > 0 or #body.body > 0
end

local function normalize_repeating_header(tbl)
  local rows = tbl.head.rows
  if #rows <= 1 or #tbl.bodies == 0 then
    return 0
  end

  for _, body in ipairs(tbl.bodies) do
    if has_rows(body) then
      return 0
    end
  end

  local body_rows = {}
  for index = 2, #rows do
    body_rows[#body_rows + 1] = rows[index]
  end

  tbl.head = pandoc.TableHead({ rows[1] }, tbl.head.attr)
  local body = tbl.bodies[1]
  body.head = {}
  body.body = body_rows
  body.row_head_columns = 0
  tbl.bodies = { body }
  return #body_rows
end

local function all_table_rows(tbl)
  local rows = {}
  for _, row in ipairs(tbl.head.rows) do
    rows[#rows + 1] = row
  end
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.head) do
      rows[#rows + 1] = row
    end
    for _, row in ipairs(body.body) do
      rows[#rows + 1] = row
    end
  end
  for _, row in ipairs(tbl.foot.rows) do
    rows[#rows + 1] = row
  end
  return rows
end

local function substantive_column_count(tbl)
  local used = {}
  for _, row in ipairs(all_table_rows(tbl)) do
    local column = 1
    for _, cell in ipairs(row.cells) do
      local span = cell.col_span or 1
      local text = pandoc.utils.stringify(cell.contents):gsub("%s+", "")
      if text ~= "" then
        for offset = 0, span - 1 do
          used[column + offset] = true
        end
      end
      column = column + span
    end
  end

  local count = 0
  for column = 1, #tbl.colspecs do
    if used[column] then
      count = count + 1
    end
  end
  return count
end

local function collapse_fully_empty_columns(tbl)
  local column_count = #tbl.colspecs
  local rows = all_table_rows(tbl)
  if column_count == 0 or #rows == 0 then
    return 0
  end

  local used = {}
  for _, row in ipairs(rows) do
    if #row.cells ~= column_count then
      return 0
    end
    for column, cell in ipairs(row.cells) do
      if (cell.col_span or 1) ~= 1 or (cell.row_span or 1) ~= 1 then
        return 0
      end
      local text = pandoc.utils.stringify(cell.contents):gsub("%s+", "")
      if text ~= "" then
        used[column] = true
      end
    end
  end

  local keep = {}
  for column = 1, column_count do
    if used[column] then
      keep[#keep + 1] = column
    end
  end
  if #keep == 0 or #keep == column_count then
    return 0
  end

  local colspecs = {}
  local width_total = 0
  local numeric_widths = true
  for _, column in ipairs(keep) do
    colspecs[#colspecs + 1] = tbl.colspecs[column]
    local width = tbl.colspecs[column][2]
    if type(width) == "number" then
      width_total = width_total + width
    else
      numeric_widths = false
    end
  end
  if numeric_widths and width_total > 0 then
    for _, colspec in ipairs(colspecs) do
      colspec[2] = colspec[2] / width_total
    end
  end
  tbl.colspecs = colspecs

  for _, row in ipairs(rows) do
    local cells = {}
    for _, column in ipairs(keep) do
      cells[#cells + 1] = row.cells[column]
    end
    row.cells = cells
  end
  return column_count - #keep
end

local function has_class(element, wanted)
  for _, class_name in ipairs(element.classes) do
    if class_name == wanted then
      return true
    end
  end
  return false
end

function Table(tbl)
  table_number = table_number + 1
  local original_columns = #tbl.colspecs
  local removed_columns = collapse_fully_empty_columns(tbl)
  local moved_rows = normalize_repeating_header(tbl)
  local columns = #tbl.colspecs
  local substantive = substantive_column_count(tbl)

  local landscape = substantive > landscape_threshold or has_class(tbl.attr, "landscape")
  if forced_landscape[table_number] then
    landscape = true
  elseif forced_portrait[table_number] or has_class(tbl.attr, "portrait") then
    landscape = false
  end
  local orientation = landscape and "landscape" or "portrait"

  io.stderr:write(string.format(
    "[elegant-print] table %d: original_columns=%d columns=%d substantive=%d orientation=%s removed_empty_columns=%d moved_header_rows=%d\n",
    table_number,
    original_columns,
    columns,
    substantive,
    orientation,
    removed_columns,
    moved_rows
  ))

  local begin_table = "\\begingroup\n\\small\n\\arrayrulecolor{Accent}"
  local end_table = "\\endgroup"
  if landscape then
    return {
      pandoc.RawBlock("latex", "\\begin{landscape}"),
      pandoc.RawBlock("latex", begin_table),
      tbl,
      pandoc.RawBlock("latex", end_table),
      pandoc.RawBlock("latex", "\\end{landscape}"),
    }
  end
  return {
    pandoc.RawBlock("latex", begin_table),
    tbl,
    pandoc.RawBlock("latex", end_table),
  }
end

function Image(image)
  -- DOCX exports store page-relative dimensions that can be wider than the
  -- Elegant Print text block.  Pandoc's bounded-image wrapper will retain the
  -- natural size for small images and shrink oversized ones to the measure.
  image.attributes.width = nil
  image.attributes.height = nil
  return image
end

function Para(paragraph)
  -- Google Docs can put a full-width image and the prose that follows it in a
  -- single paragraph.  Splitting that shape keeps the bounded image on its own
  -- line and prevents the following prose from extending the image box.  The
  -- no-indent marker also gives the bounded image the full current measure.
  if #paragraph.content > 0 and paragraph.content[1].tag == "Image" then
    local image_paragraph = pandoc.Para({
      pandoc.RawInline("latex", "\\noindent"),
      paragraph.content[1],
    })
    if #paragraph.content == 1 then
      return image_paragraph
    end
    local prose = {}
    for index = 2, #paragraph.content do
      prose[#prose + 1] = paragraph.content[index]
    end
    return {
      image_paragraph,
      pandoc.Para(prose),
    }
  end
  return paragraph
end

local function landscape_start(block)
  return block.tag == "RawBlock"
    and block.format == "latex"
    and block.text == "\\begin{landscape}"
end

local function landscape_end(block)
  return block.tag == "RawBlock"
    and block.format == "latex"
    and block.text == "\\end{landscape}"
end

local function short_context(block)
  if block.tag == "Header" then
    return true
  end
  if block.tag ~= "Para" and block.tag ~= "Plain" then
    return false
  end
  local text = pandoc.utils.stringify(block)
  local words = 0
  for _ in string.gmatch(text, "%S+") do
    words = words + 1
  end
  return words <= 80
end

function Pandoc(document)
  local blocks = {}
  for _, block in ipairs(document.blocks) do
    if landscape_start(block) then
      local context = {}
      if #blocks > 0 and short_context(blocks[#blocks]) then
        table.insert(context, 1, table.remove(blocks))
      end
      if #context > 0
        and context[1].tag ~= "Header"
        and #blocks > 0
        and blocks[#blocks].tag == "Header" then
        table.insert(context, 1, table.remove(blocks))
      end

      blocks[#blocks + 1] = block
      for _, context_block in ipairs(context) do
        blocks[#blocks + 1] = context_block
      end
    else
      blocks[#blocks + 1] = block
    end
  end

  local merged = {}
  local index = 1
  while index <= #blocks do
    if landscape_end(blocks[index])
      and index < #blocks
      and landscape_start(blocks[index + 1]) then
      index = index + 2
    else
      merged[#merged + 1] = blocks[index]
      index = index + 1
    end
  end

  document.blocks = merged
  return document
end
