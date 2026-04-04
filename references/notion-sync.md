# Notion Sync Reference

Use this reference only when preparing the final article for Notion.

## Preparation

Before pushing:
1. Strip YAML frontmatter from the body content
2. Use the YAML title as the Notion page title
3. Remove any internal review section
4. Replace local image paths with hosted URLs
5. Keep the article body free of duplicate top-level titles

## Supported markdown patterns

| Markdown | Notion block |
|---|---|
| Plain paragraph | paragraph |
| `## Heading` | heading_2 |
| `- item` | bulleted_list_item |
| `1. item` | numbered_list_item |
| `> quote` | quote |
| `![alt](url)` | image |
| fenced code block | code |
| `---` | divider |
| markdown table | table + table_row |

## Critical constraints

- Table rows must become flat rich_text arrays, not nested arrays.
- Separator rows must be filtered correctly.
- Database IDs must use the canonical dashed form.
- Upload assets sequentially when the environment is prone to file-lock or iCloud sync issues.

## Property mapping

Keep property mapping outside the core workflow when it is deployment-specific. For hamster's current deployment, map at least:
- Name
- source URL
- tags
- lead visual
- personal reflection field

## Validation

After pushing:
- verify the page exists
- verify block count looks sane
- inspect tables separately if used
- confirm image URLs render correctly
