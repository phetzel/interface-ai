"""Bounded goal-driven provider loop. No scripted UI path or business-result parsing."""

import time
from .discovery_request import DiscoveryRequest

from .discovery import (
    MODEL,
    ProbeError,
    append_observation,
    image_url,
    provider_error,
    response_metadata,
    selected_call,
)


def goal(member):
    return DiscoveryRequest.parse(member_id=member).prompt()


def run_discovery(client, transport, report, save, member, *, request=None, clock=time.monotonic):
    request = request or DiscoveryRequest.parse(member_id=member)
    if request.member_id != member:
        raise ProbeError('invalid_input')
    started = clock()
    frame = transport.post('start', {'session': transport.session, 'memberId': member})
    report.update(
        sessionId=transport.session, runId=frame['lease']['runId'], desktopRun=frame['directory']
    )
    history = [
        {
            'role': 'user',
            'content': [
                {'type': 'input_text', 'text': request.prompt()},
                {'type': 'input_image', 'image_url': image_url(frame), 'detail': 'original'},
            ],
        }
    ]
    while True:
        if report['requestsAttempted'] >= 20 or clock() - started >= 120:
            raise ProbeError('discovery_budget')
        transport.post('check', {'lease': frame['lease']})
        report['requestsAttempted'] += 1
        report['usageUnknown'] = True
        save()
        try:
            response = client.responses.create(
                model=MODEL,
                tools=[{'type': 'computer'}],
                input=history,
                tool_choice='required',
                store=False,
                include=['reasoning.encrypted_content'],
                max_output_tokens=1800,
            ).model_dump(exclude_none=True)
        except Exception as exc:
            raise ProbeError(provider_error(exc)) from None
        report['responsesCompleted'] += 1
        metadata = response_metadata(response)
        report['responses'].append(metadata)
        report['usageUnknown'] = any(len(item['usage']) != 3 for item in report['responses'])
        save()
        if metadata['model'] != MODEL:
            raise ProbeError('provider_model_mismatch')
        call = selected_call(response)
        actions = call.get('actions')
        if not isinstance(actions, list) or not 1 <= len(actions) <= 4:
            raise ProbeError('unsupported_action_batch')
        # Lease predates the network request; the desktop checks every primitive.
        report.update(
            lastAcknowledgedActions=frame['actionsCompleted'],
            actionsCompleted=None,
            inputDispatchUncertain=True,
        )
        save()
        frame = transport.post(
            'propose',
            {
                'lease': frame['lease'],
                'actions': actions,
                'callId': call['call_id'],
                'responseId': metadata['id'],
            },
        )
        report['actionsCompleted'] = frame['actionsCompleted']
        report['lastAcknowledgedActions'] = frame['actionsCompleted']
        report['inputDispatchUncertain'] = False
        if frame.get('result') is not None:
            report['candidate'] = frame.get('candidate')
            report['status'] = 'passed' if frame['result']['status'] == 'success' else 'failed'
            report['resultStatus'] = frame['result']['status']
            save()
            return frame['result']
        append_observation(history, response, call['call_id'], frame)
