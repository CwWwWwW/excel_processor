# Excel Processor 1.0.1 Release Notes

This release hardens the v1.0.0 skeleton into a transactional local Windows Excel processor foundation. It does not bundle Microsoft Excel; Excel is detected at runtime. Without Excel, the app starts in limited OpenXML/CSV mode and COM-only operations fail closed.
