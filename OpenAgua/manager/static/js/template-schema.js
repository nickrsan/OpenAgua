var schema =
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "cr_date": {
      "type": "string"
    },
    "id": {
      "type": "integer",
      "default": -1
    },
    "layout": {
      "type": "object",
      "properties": {}
    },
    "name": {
      "type": "string"
    },
    "types": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "cr_date": {
            "type": "string"
          },
          "id": {
            "type": "integer"
          },
          "layout": {
            "type": "object",
            "properties": {
              "image": {
                "type": "string"
              }
            },
            "required": [
              "image"
            ]
          },
          "name": {
            "type": "string"
          },
          "resource_type": {
            "type": "string"
          },
          "template_id": {
            "type": "integer"
          },
          "typeattrs": {
            "type": "array",
            "format": "table",
            "items": {
              "type": "object",
              "properties": {
                "attr_id": {
                  "type": "integer"
                },
                "attr_name": {
                  "type": "string"
                },
                "cr_date": {
                  "type": "string"
                },
                "data_restriction": {
                  "type": "object",
                  "properties": {}
                },
                "data_type": {
                  "type": "string"
                },
                "dimension": {
                  "type": "string"
                },
                "is_var": {
                  "type": "string"
                },
                "properties": {
                  "type": "object",
                  "properties": {}
                },
                "type_id": {
                  "type": "integer"
                },
                "unit": {
                  "type": "string"
                }
              },
              "required": [
                "attr_id",
                "attr_name",
                "cr_date",
                "data_restriction",
                "data_type",
                "dimension",
                "is_var",
                "properties",
                "type_id",
                "unit"
              ]
            }
          }
        },
        "required": [
          "cr_date",
          "id",
          "layout",
          "name",
          "resource_type",
          "template_id",
          "typeattrs"
        ]
      }
    }
  },
  "required": [
    "cr_date",
    "id",
    "layout",
    "name",
    "types"
  ]
};