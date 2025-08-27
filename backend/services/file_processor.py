"""
📁 File Processor for handling uploads
Processes WhatsApp exports, audio files, and text documents
"""

from fastapi import UploadFile
from typing import Dict, List, Any, Optional
import asyncio
import json
import zipfile
import io
import os
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

class FileProcessor:
    """Handles file upload and processing"""
    
    def __init__(self):
        self.supported_formats = {
            'text/plain': self._process_text,
            'application/zip': self._process_zip,
            'audio/opus': self._process_audio,
            'audio/ogg': self._process_audio,
            'application/json': self._process_json
        }
    
    async def process_file(self, file: UploadFile) -> Dict[str, Any]:
        """Process uploaded file based on content type"""
        try:
            logger.info(f"📁 Processing file: {file.filename} ({file.content_type})")
            
            # Read file content
            content = await file.read()
            
            # Process based on content type
            if file.content_type in self.supported_formats:
                processor = self.supported_formats[file.content_type]
                result = await processor(content, file.filename)
            else:
                # Try to process as text if unknown type
                result = await self._process_text(content, file.filename)
            
            result['metadata'] = {
                'filename': file.filename,
                'content_type': file.content_type,
                'size': len(content),
                'processed_at': logger._formatTime(logger.handlers[0].formatter, logger.handlers[0].formatter.converter(asyncio.get_event_loop().time()))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing file {file.filename}: {str(e)}")
            raise
    
    async def _process_text(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process plain text file"""
        try:
            text = content.decode('utf-8')
            return {
                'type': 'text',
                'content': text,
                'messages': [{'content': text, 'timestamp': None, 'sender': 'unknown'}]
            }
        except UnicodeDecodeError:
            return {
                'type': 'text',
                'content': content.decode('utf-8', errors='ignore'),
                'messages': [{'content': 'Binary content converted to text', 'timestamp': None, 'sender': 'system'}]
            }
    
    async def _process_zip(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process ZIP file (WhatsApp export)"""
        try:
            with zipfile.ZipFile(io.BytesIO(content), 'r') as zip_file:
                messages = []
                
                for file_info in zip_file.filelist:
                    if file_info.filename.endswith('.txt'):
                        # Process WhatsApp chat export
                        with zip_file.open(file_info.filename) as chat_file:
                            chat_content = chat_file.read().decode('utf-8')
                            messages.extend(self._parse_whatsapp_export(chat_content))
                
                return {
                    'type': 'whatsapp_export',
                    'content': f"WhatsApp export with {len(messages)} messages",
                    'messages': messages
                }
        except Exception as e:
            logger.error(f"Error processing ZIP file: {e}")
            return await self._process_text(content, filename)
    
    async def _process_audio(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process audio file (placeholder for STT)"""
        # This would integrate with Whisper or other STT service
        return {
            'type': 'audio',
            'content': f"Audio file: {filename} ({len(content)} bytes)",
            'messages': [{'content': '[Audio transcription would go here]', 'timestamp': None, 'sender': 'audio'}],
            'audio_metadata': {
                'size': len(content),
                'format': 'opus' if filename.endswith('.opus') else 'ogg'
            }
        }
    
    async def _process_json(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process JSON file"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            if isinstance(data, list) and all('content' in item for item in data if isinstance(item, dict)):
                # Looks like a message list
                return {
                    'type': 'json_messages',
                    'content': f"JSON file with {len(data)} items",
                    'messages': data
                }
            else:
                return {
                    'type': 'json_data',
                    'content': json.dumps(data, indent=2),
                    'messages': [{'content': json.dumps(data), 'timestamp': None, 'sender': 'json'}]
                }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {e}")
            return await self._process_text(content, filename)
    
    def _parse_whatsapp_export(self, content: str) -> List[Dict[str, Any]]:
        """Parse WhatsApp chat export format"""
        messages = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple WhatsApp format parsing (can be enhanced)
            if '] ' in line and ': ' in line:
                try:
                    timestamp_part, rest = line.split('] ', 1)
                    timestamp = timestamp_part[1:]  # Remove leading [
                    
                    if ': ' in rest:
                        sender, message = rest.split(': ', 1)
                        messages.append({
                            'timestamp': timestamp,
                            'sender': sender,
                            'content': message
                        })
                except ValueError:
                    # Malformed line, skip
                    continue
        
        logger.info(f"📱 Parsed {len(messages)} WhatsApp messages")
        return messages